#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliJrpcClntBt:
    """Integration test for the `ottopi0 bt` CLI command."""

    @pytest.fixture
    def mock_bt_app(self):
        with mock.patch("ottopi0.clnt.bt.Bt") as MockApp:
            yield MockApp

    def test_cli_invocation_default(self, mock_bt_app):
        """Test invoking the command with default arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["bt"])

        assert result.exit_code == 0
        assert "Done." in result.output

        # Verify app was initialized with default args
        mock_bt_app.assert_called_once()
        args, kwargs = mock_bt_app.call_args

        # Check btdev_keyword (first arg) - should be a list
        assert isinstance(args[0], list)
        # Check URL contains http protocol (second arg)
        assert "http://" in args[1]

        # Verify app.main() and app.end() were called
        mock_bt_app.return_value.main.assert_called_once()
        mock_bt_app.return_value.end.assert_called_once()

    def test_cli_invocation_custom(self, mock_bt_app):
        """Test invoking the command with custom arguments."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bt",
                "--btdev",
                "PS4,Controller",
                "--host",
                "192.168.1.100",
                "--port",
                "8888",
                "--apipath",
                "/api/cmd",
            ],
        )

        assert result.exit_code == 0

        mock_bt_app.assert_called_once()
        args, kwargs = mock_bt_app.call_args

        # Check btdev_keyword
        assert args[0] == ["PS4", "Controller"]

        # Check URL construction
        expected_url = "http://192.168.1.100:8888/api/cmd"
        assert args[1] == expected_url

    def test_cli_exception_handling(self, mock_bt_app):
        """Test how the CLI handles exceptions during app run."""
        mock_bt_app.return_value.main.side_effect = Exception("Crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["bt"])

        assert (
            result.exit_code == 0
        )  # Command itself doesn't crash, it catches exception
        # Check that "Done." is printed in finally block
        assert "Done." in result.output

        # Verify app.end() was still called despite exception
        mock_bt_app.return_value.end.assert_called_once()

    def test_cli_short_options(self, mock_bt_app):
        """Test invoking the command with short option flags."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bt",
                "-b",
                "Xbox,Wireless",
                "-i",
                "localhost",
                "-p",
                "9999",
                "-a",
                "/custom/api",
            ],
        )

        assert result.exit_code == 0

        mock_bt_app.assert_called_once()
        args, kwargs = mock_bt_app.call_args

        # Check btdev_keyword
        assert args[0] == ["Xbox", "Wireless"]

        # Check URL construction
        expected_url = "http://localhost:9999/custom/api"
        assert args[1] == expected_url

    def test_cli_btdev_argument(self, mock_bt_app):
        """Test invoking the command with btdev as positional argument."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bt",
                "Switch",
                "Pro",
            ],
        )

        assert result.exit_code == 0

        mock_bt_app.assert_called_once()
        args, kwargs = mock_bt_app.call_args

        # Note: btdev_keyword argument is processed but --btdev option takes precedence
        # Check that URL was constructed
        assert "http://" in args[1]
