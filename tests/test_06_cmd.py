#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from ottopi0.clnt.cmd import Cmd


class TestJrpcClntCli:
    """
    Test class for JrpcClntCli
    """

    @pytest.fixture
    def mock_deps(self):
        """
        Mock dependencies: JrpcClient, readline, os
        """
        with (
            patch("ottopi0.clnt.cmd.Client") as MockJrpcClient,
            patch("ottopi0.clnt.cmd.readline") as MockReadline,
            patch("ottopi0.clnt.cmd.os") as MockOs,
        ):
            yield {
                "JrpcClient": MockJrpcClient,
                "readline": MockReadline,
                "os": MockOs,
            }

    def test_init(self, mock_deps):
        """
        Test initialization and history file loading.
        """
        cli_obj = Cmd("history_file", "http://url")

        assert cli_obj.url == "http://url"
        mock_deps["readline"].read_history_file.assert_called()

    def test_main_loop_command(self, mock_deps):
        """
        Test main loop processing a command.
        """
        cli_obj = Cmd("history_file", "http://url")

        # Mock input to return a command then EOF (raise EOFError to simulate Ctrl-D eventually, or just let loop break?
        # The code catches EOFError and breaks.
        with patch("builtins.input", side_effect=["cmd1", EOFError()]):
            cli_obj.main()

        # Check if jrpc_call was called with "cmd1"
        cast(MagicMock, cli_obj.jrpcclnt.jrpc_call).assert_called_with("cmd1")

    def test_main_loop_comment(self, mock_deps):
        """
        Test comment removal in main loop.
        """
        cli_obj = Cmd("history_file", "http://url")

        with patch(
            "builtins.input", side_effect=["cmd # comment", EOFError()]
        ):
            cli_obj.main()

        # "cmd # comment" -> "cmd " (partition keeps separator? no, [0] is before separator)
        # "cmd # comment".partition("#")[0] -> "cmd "
        cast(MagicMock, cli_obj.jrpcclnt.jrpc_call).assert_called_with("cmd ")

    def test_end_saves_history(self, mock_deps):
        """
        Test end method saves history.
        """
        cli_obj = Cmd("history_file", "http://url")
        cli_obj.end()

        mock_deps["readline"].write_history_file.assert_called()

    def test_init_no_history_file(self, mock_deps):
        """
        Test init when history file is missing (FileNotFoundError).
        """
        mock_deps[
            "readline"
        ].read_history_file.side_effect = FileNotFoundError

        cli_obj = Cmd("history_file", "http://url")
        # Should handle exception and log warning (asserting log could be done if we mocked get_logger)
        # Main thing is it doesn't crash
        assert cli_obj.is_active

    def test_init_invalid_history_file(self, mock_deps):
        """
        Test init with invalid history file (OSError) -> removes file.
        """
        mock_deps["readline"].read_history_file.side_effect = OSError

        _ = Cmd("history_file", "http://url")

        mock_deps["os"].remove.assert_called()
