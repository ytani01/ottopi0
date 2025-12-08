#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from ottopi0.jrpcclnt.jrpcclnt_bt import JrpcClntBt


class TestJrpcClntBt:
    """
    Test class for JrpcClntBt in jrpcclnt_bt.py
    """

    @pytest.fixture
    def mock_deps(self):
        """
        Mock dependencies: PiBtInput, JrpcClient, CmdStrLib, ConfFile
        """
        with (
            patch("ottopi0.jrpcclnt.jrpcclnt_bt.PiBtInput") as MockPiBtInput,
            patch(
                "ottopi0.jrpcclnt.jrpcclnt_bt.JrpcClient"
            ) as MockJrpcClient,
            patch("ottopi0.jrpcclnt.jrpcclnt_bt.CmdStrLib") as MockCmdStrLib,
            patch("ottopi0.jrpcclnt.jrpcclnt_bt.ConfFile") as MockConfFile,
        ):
            # Setup Mock ConfFile
            mock_conf_instance = MockConfFile.return_value
            mock_conf = MagicMock()
            mock_conf_instance.conf = mock_conf

            # Default config structure
            mock_conf.servo.funcs = {"_prefix": "prefix:"}
            mock_conf.jrpc.client.bluetooth.get.return_value = {}  # Default empty keys

            # Setup Mock CmdStrLib
            mock_cslib_instance = MockCmdStrLib.return_value
            # return the input string as expanded for simplicity, or modify as needed
            mock_cslib_instance.expand_func.side_effect = lambda x: x

            yield {
                "PiBtInput": MockPiBtInput,
                "JrpcClient": MockJrpcClient,
                "CmdStrLib": MockCmdStrLib,
                "ConfFile": MockConfFile,
                "conf": mock_conf,
                "cslib": mock_cslib_instance,
            }

    def test_mk_keymap_normalization(self, mock_deps):
        """
        Test that mk_keymap normalizes 'KEY_B-KEY_A' to 'KEY_A-KEY_B'.
        """
        # Arrange
        keys_config = {
            "KEY_A": "cmd_a",
            "KEY_B-KEY_A": "cmd_ab",  # Unsorted in config
            "KEY_X-KEY_Y-KEY_Z": "cmd_xyz",
        }
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config

        # Act
        # Initialize JrpcClntBt (will call mk_keymap)
        clnt = JrpcClntBt("dummy_keyword", "http://dummy")

        # Assert
        # Check if keys are normalized in self.keymap
        # Prefix is "prefix:"
        assert "KEY_A" in clnt.keymap
        assert clnt.keymap["KEY_A"] == "prefix: cmd_a"

        # "KEY_B-KEY_A" should be stored as "KEY_A-KEY_B"
        assert "KEY_A-KEY_B" in clnt.keymap
        assert "KEY_B-KEY_A" not in clnt.keymap
        assert clnt.keymap["KEY_A-KEY_B"] == "prefix: cmd_ab"

        # 3 keys
        assert "KEY_X-KEY_Y-KEY_Z" in clnt.keymap

    def test_cb_ev_single_key(self, mock_deps):
        """
        Test callback with single key press.
        """
        # Arrange
        keys_config = {"KEY_A": "cmd_a"}
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = JrpcClntBt("dummy_keyword", "http://dummy")

        # Mock key event
        key_name = "KEY_A"

        # down
        # (not handled specifically in logic, but checks keys["up"]/["hold"])
        key_state = 1

        # PiBtInput.KEY["up"] is typically 0,
        # "hold" is 2. Let's assume 1 is down.
        # We need to ensure we don't hit "up" or "hold" returns.
        # Need to know values of PiBtInput.KEY.
        # Since we mocked PiBtInput,
        # checking the class attribute access in code:
        # if key_state == PiBtInput.KEY["up"]:
        # We should set the mocked PiBtInput.KEY dict.
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        onkeys = {"KEY_A": 123}  # dict of key:keycode

        # Act
        clnt.cb_ev(key_name, key_state, onkeys)

        # Assert
        # Should call jrpc_call with mapped command
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_a"
        )

    def test_cb_ev_chord(self, mock_deps):
        """
        Test callback with simultaneous key press (chord).
        """
        # Arrange
        keys_config = {
            "KEY_A": "cmd_a",
            "KEY_B": "cmd_b",
            # Normalized key in config implies code will normalize it too
            # if written as B-A
            "KEY_A-KEY_B": "cmd_ab",
        }
        # Let's test providing B-A in config too to ensure normalization works there
        keys_config["KEY_D-KEY_C"] = "cmd_cd"

        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = JrpcClntBt("dummy_keyword", "http://dummy")
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        # Case 1: A and B pressed
        onkeys = {"KEY_B": 1, "KEY_A": 1}  # Order in dict shouldn't matter
        clnt.cb_ev(
            "KEY_B", 1, onkeys
        )  # Triggered by B down, while A is already down

        # Assert
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_ab"
        )

        # Case 2: C and D pressed (Config has D-C)
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).reset_mock()
        onkeys = {"KEY_C": 1, "KEY_D": 1}
        clnt.cb_ev("KEY_D", 1, onkeys)

        # Assert
        # "KEY_D-KEY_C" in config -> normalized to "KEY_C-KEY_D" in keymap
        # onkeys "C", "D" -> sorted "C", "D" -> joined "KEY_C-KEY_D"
        # keymap["KEY_C-KEY_D"] -> "prefix: cmd_cd"
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_cd"
        )

    def test_cb_ev_no_match(self, mock_deps):
        """
        Test callback with no matching key/chord.
        """
        keys_config = {"KEY_A": "cmd_a"}
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = JrpcClntBt("dummy_keyword", "http://dummy")
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        # Press Z (not mapped)
        onkeys = {"KEY_Z": 1}
        clnt.cb_ev("KEY_Z", 1, onkeys)

        # Assert
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_not_called()

        # Press A+B (only A mapped, chord not mapped)
        # Current logic: _current_combo = "KEY_A-KEY_B".
        # If not found, it falls back to single key processing?
        # The user commented out the single key fallback!
        # with fallback commented out:
        # _cmd_str = keymap.get("KEY_A-KEY_B") -> None
        # jrpc_call not called.

        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).reset_mock()
        onkeys = {"KEY_A": 1, "KEY_B": 1}
        clnt.cb_ev("KEY_B", 1, onkeys)

        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_not_called()
