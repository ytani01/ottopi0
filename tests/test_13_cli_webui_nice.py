#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliWebUiNice:
    """Integration test for the `ottopi0 jrpcclnt_webui_nice` CLI command."""

    @pytest.fixture
    def mock_nice_app(self):
        with mock.patch(
            "ottopi0.jrpcclnt.jrpcclnt_webui_nice.JrpcClntWebUiNice"
        ) as MockApp:
            yield MockApp

    def test_cli_invocation_default(self, mock_nice_app):
        """Test invoking the command with default arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["jrpcclnt_webui_nice"])

        assert result.exit_code == 0
        assert "Done." in result.output

        # Verify app was initialized with default args
        mock_nice_app.assert_called_once()
        args, kwargs = mock_nice_app.call_args

        # Check URL contains http protocol
        assert "http://" in args[0]
        # Check that webui_port kwarg was passed
        assert "webui_port" in kwargs

        # Verify app.run() was called
        mock_nice_app.return_value.run.assert_called_once()

    def test_cli_invocation_custom(self, mock_nice_app):
        """Test invoking the command with custom arguments."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "jrpcclnt_webui_nice",
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

        mock_nice_app.assert_called_once()
        args, kwargs = mock_nice_app.call_args

        # Check URL construction
        expected_url = "http://192.168.1.100:8888/api/cmd"
        assert args[0] == expected_url

        # Check WebUI port
        assert kwargs.get("webui_port") == 9000

    def test_cli_exception_handling(self, mock_nice_app):
        """Test how the CLI handles exceptions during app run."""
        mock_nice_app.return_value.run.side_effect = Exception("Crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["jrpcclnt_webui_nice"])

        assert (
            result.exit_code == 0
        )  # Command itself doesn't crash, it catches exception
        # Check that error was logged/printed.
        # ClickRunner captures stdout, logs might go to stderr or be captured.
        # Our CLI prints "Done." in finally block.
        assert "Done." in result.output
