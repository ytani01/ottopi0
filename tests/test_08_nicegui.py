#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest

from ottopi0.clnt.nicegui import NiceGUI


class TestJrpcClntWebUiNice:
    @pytest.fixture
    def mock_jrpc_client(self):
        with mock.patch("ottopi0.clnt.nicegui.Client") as MockClient:
            yield MockClient

    @pytest.fixture
    def mock_ui(self):
        with mock.patch("ottopi0.clnt.nicegui.ui") as MockUI:
            yield MockUI

    def test_init(self, mock_jrpc_client, mock_ui):
        """Test initialization and command loading."""
        with (
            mock.patch("ottopi0.clnt.nicegui.ConfFile") as MockConfFile,
            mock.patch("ottopi0.clnt.nicegui.CmdStrLib") as MockCmdStrLib,
        ):
            # Setup Mock Config
            mock_conf = MockConfFile.return_value.conf
            mock_conf.servo.funcs = {"_prefix": "PREFIX"}
            mock_conf.get.side_effect = (
                lambda k, d=None: {
                    "client": {
                        "webui": {"buttons": {"forward": "NICE_FORWARD"}}
                    }
                }
                if k == "jrpc"
                else d
            )

            # Setup Mock CmdStrLib
            MockCmdStrLib.return_value.expand_func.side_effect = (
                lambda x: f"EXPANDED:{x}"
            )

            # Initialize
            app = NiceGUI("http://host:1234/api", 5001)

            # Check if JrpcClient initialized
            mock_jrpc_client.assert_called_with(
                "http://host:1234/api", debug=False
            )

            # Check command expansion
            # "NICE_FORWARD" -> "PREFIX NICE_FORWARD" -> "EXPANDED:PREFIX NICE_FORWARD"
            assert "EXPANDED:PREFIX NICE_FORWARD" in app.cmd_forward
            # Missing command should be empty
            assert app.cmd_backward == ""

    def test_send_cmd(self, mock_jrpc_client, mock_ui):
        """Test sending a command."""
        # Need to init app first
        with (
            mock.patch("ottopi0.clnt.nicegui.ConfFile"),
            mock.patch("ottopi0.clnt.nicegui.CmdStrLib"),
        ):
            app = NiceGUI("http://host:1234/api", 5001)

            # 1. Send valid command
            mock_client_instance = mock_jrpc_client.return_value
            mock_client_instance.url = "http://host:1234/api"

            app.send_cmd("TEST_CMD")

            mock_client_instance.jrpc_call.assert_called_with("TEST_CMD")

            # 2. Send empty command
            mock_client_instance.jrpc_call.reset_mock()
            app.send_cmd("")
            mock_client_instance.jrpc_call.assert_not_called()

    def test_log_message(self, mock_jrpc_client, mock_ui):
        """Test logging to UI."""
        with (
            mock.patch("ottopi0.clnt.nicegui.ConfFile"),
            mock.patch("ottopi0.clnt.nicegui.CmdStrLib"),
        ):
            app = NiceGUI("http://host", 5001)

            # Mock log container context manager
            app.log_container = mock.MagicMock()

            app.log_message("Hello")

            app.log_container.__enter__.assert_called()
            mock_ui.label.assert_called()
            arg = mock_ui.label.call_args[0][0]
            assert "Hello" in arg

    def test_build_ui(self, mock_jrpc_client, mock_ui):
        """Test UI building calls."""
        with (
            mock.patch("ottopi0.clnt.nicegui.ConfFile"),
            mock.patch("ottopi0.clnt.nicegui.CmdStrLib"),
        ):
            app = NiceGUI("http://host", 5001)
            app.build_ui()

            # Verify basic UI elements were created
            mock_ui.header.assert_called()
            mock_ui.button.assert_called()
            mock_ui.input.assert_called()
