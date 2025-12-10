#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliWebUI:
    """Integration test for the `ottopi0 webui` CLI command."""

    @pytest.fixture
    def mock_webui_app(self):
        with mock.patch("ottopi0.clnt.webui.WebUI") as MockApp:
            yield MockApp

    def test_cli_invocation_default(self, mock_webui_app):
        """Test invoking the command with default arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["webui"])

        assert result.exit_code == 0
        assert "Done." in result.output

        # Verify app was initialized with default args
        mock_webui_app.assert_called_once()
        args, kwargs = mock_webui_app.call_args

        # Check URL contains http protocol
        assert "http://" in args[0]
        # Check that webui_port kwarg was passed
        assert "webui_port" in kwargs

        # Verify app.run() was called
        mock_webui_app.return_value.run.assert_called_once()

    def test_cli_invocation_custom(self, mock_webui_app):
        """Test invoking the command with custom arguments."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "webui",
                "--host",
                "192.168.1.100",
                "--port",
                "8888",
                "--apipath",
                "/api/cmd",
                "--webui-port",
                "9000",
            ],
        )

        assert result.exit_code == 0

        mock_webui_app.assert_called_once()
        args, kwargs = mock_webui_app.call_args

        # Check URL construction
        expected_url = "http://192.168.1.100:8888/api/cmd"
        assert args[0] == expected_url

        # Check WebUI port
        assert kwargs.get("webui_port") == 9000

    def test_cli_exception_handling(self, mock_webui_app):
        """Test how the CLI handles exceptions during app run."""
        mock_webui_app.return_value.run.side_effect = Exception("Crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["webui"])

        assert (
            result.exit_code == 0
        )  # Command itself doesn't crash, it catches exception
        # Check that error was logged/printed.
        # ClickRunner captures stdout, logs might go to stderr or be captured.
        # Our CLI prints "Done." in finally block.
        assert "Done." in result.output
