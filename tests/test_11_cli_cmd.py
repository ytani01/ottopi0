#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliJrpcClntCli:
    """Integration test for the `ottopi0 cmd` CLI command."""

    @pytest.fixture
    def mock_cli_app(self):
        with mock.patch("ottopi0.clnt.cmd.Cmd") as MockApp:
            yield MockApp

    def test_cli_invocation_default(self, mock_cli_app):
        """Test invoking the command with default arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["cmd"])

        assert result.exit_code == 0
        assert "Done." in result.output

        # Verify app was initialized with default args
        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # Check history file (first arg)
        assert args[0] is not None
        # Check URL contains http protocol (second arg)
        assert "http://" in args[1]

        # Verify app.main() and app.end() were called
        mock_cli_app.return_value.main.assert_called_once()
        mock_cli_app.return_value.end.assert_called_once()

    def test_cli_invocation_custom(self, mock_cli_app):
        """Test invoking the command with custom arguments."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "cmd",
                "--historyfile",
                "/tmp/test_history.txt",
                "--host",
                "192.168.1.100",
                "--port",
                "8888",
                "--apipath",
                "/api/cmd",
            ],
        )

        assert result.exit_code == 0

        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # Check history file
        assert args[0] == "/tmp/test_history.txt"

        # Check URL construction
        expected_url = "http://192.168.1.100:8888/api/cmd"
        assert args[1] == expected_url

    def test_cli_exception_handling(self, mock_cli_app):
        """Test how the CLI handles exceptions during app run."""
        mock_cli_app.return_value.main.side_effect = Exception("Crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["cmd"])

        assert (
            result.exit_code == 0
        )  # Command itself doesn't crash, it catches exception
        # Check that error was logged/printed.
        # ClickRunner captures stdout, logs might go to stderr or be captured.
        # Our CLI prints "Done." in finally block.
        assert "Done." in result.output

        # Verify app.end() was still called despite exception
        mock_cli_app.return_value.end.assert_called_once()

    def test_cli_short_options(self, mock_cli_app):
        """Test invoking the command with short option flags."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "cmd",
                "--hist",
                "/tmp/hist.txt",
                "-i",
                "localhost",
                "-p",
                "9999",
                "-a",
                "/custom/api",
            ],
        )

        assert result.exit_code == 0

        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # Check history file
        assert args[0] == "/tmp/hist.txt"

        # Check URL construction
        expected_url = "http://localhost:9999/custom/api"
        assert args[1] == expected_url
