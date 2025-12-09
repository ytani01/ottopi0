#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliSvr:
    """Integration test for the `ottopi0 svr` CLI command."""

    @pytest.fixture
    def mock_uvicorn(self):
        with mock.patch("uvicorn.run") as MockUvicorn:
            yield MockUvicorn

    def test_cli_invocation_default(self, mock_uvicorn):
        """Test invoking the command with default arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["svr"])

        assert result.exit_code == 0
        assert "END." in result.output

        # Verify uvicorn.run was called with default args
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # Check that the API path is correct
        assert "ottopi0.svr.svr:api" in args

        # Check default host and port
        assert kwargs.get("host") is not None
        assert kwargs.get("port") is not None
        assert kwargs.get("reload") is False
        assert kwargs.get("log_level") == "warning"

    def test_cli_invocation_custom(self, mock_uvicorn):
        """Test invoking the command with custom arguments."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "svr",
                "--servo-pins",
                "12,13,14,15",
                "--host",
                "0.0.0.0",
                "--port",
                "9999",
                "--reload",
            ],
        )

        assert result.exit_code == 0

        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # Check custom host and port
        assert kwargs.get("host") == "0.0.0.0"
        assert kwargs.get("port") == 9999
        assert kwargs.get("reload") is True

    def test_cli_invocation_debug(self, mock_uvicorn):
        """Test invoking the command with debug flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["svr", "--debug"])

        assert result.exit_code == 0

        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # Check that log_level is set to debug
        assert kwargs.get("log_level") == "debug"

    def test_cli_exception_handling(self, mock_uvicorn):
        """Test how the CLI handles exceptions during server run."""
        mock_uvicorn.side_effect = Exception("Server crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["svr"])

        assert (
            result.exit_code == 0
        )  # Command itself doesn't crash, it catches exception
        # Check that "END." is printed in finally block
        assert "END." in result.output

    def test_cli_short_options(self, mock_uvicorn):
        """Test invoking the command with short option flags."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "svr",
                "-s",
                "10,11,12,13",
                "-i",
                "192.168.1.1",
                "-p",
                "7777",
                "-r",
            ],
        )

        assert result.exit_code == 0

        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # Check custom host and port
        assert kwargs.get("host") == "192.168.1.1"
        assert kwargs.get("port") == 7777
        assert kwargs.get("reload") is True
