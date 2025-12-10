#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from click.testing import CliRunner

from ottopi0.__main__ import cli


class TestCliSvr:
    """`ottopi0 svr` CLI コマンドの統合テスト。"""

    @pytest.fixture
    def mock_uvicorn(self):
        """uvicorn.run をモックするフィクスチャ。"""
        with mock.patch("uvicorn.run") as MockUvicorn:
            yield MockUvicorn

    def test_cli_invocation_default(self, mock_uvicorn):
        """デフォルト引数でコマンドを呼び出すテスト。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["svr"])

        assert result.exit_code == 0
        assert "END." in result.output

        # uvicorn.runがデフォルト引数で呼び出されたことを検証
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # APIパスが正しいことを確認
        assert "ottopi0.svr.svr:api" in args

        # デフォルトのホストとポートを確認
        assert kwargs.get("host") is not None
        assert kwargs.get("port") is not None
        assert kwargs.get("reload") is False
        assert kwargs.get("log_level") == "warning"

    def test_cli_invocation_custom(self, mock_uvicorn):
        """カスタム引数でコマンドを呼び出すテスト。"""
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

        # カスタムホストとポートを確認
        assert kwargs.get("host") == "0.0.0.0"
        assert kwargs.get("port") == 9999
        assert kwargs.get("reload") is True

    def test_cli_invocation_debug(self, mock_uvicorn):
        """デバッグフラグ付きでコマンドを呼び出すテスト。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["svr", "--debug"])

        assert result.exit_code == 0

        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args

        # log_levelがdebugに設定されていることを確認
        assert kwargs.get("log_level") == "debug"

    def test_cli_exception_handling(self, mock_uvicorn):
        """CLIがサーバー実行中の例外をどのように処理するかをテスト。"""
        mock_uvicorn.side_effect = Exception("Server crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["svr"])

        assert (
            result.exit_code == 0
        )  # コマンド自体はクラッシュせず、例外をキャッチする
        # finallyブロックで"END."が出力されたことを確認
        assert "END." in result.output

    def test_cli_short_options(self, mock_uvicorn):
        """ショートオプションフラグでコマンドを呼び出すテスト。"""
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

        # カスタムホストとポートを確認
        assert kwargs.get("host") == "192.168.1.1"
        assert kwargs.get("port") == 7777
        assert kwargs.get("reload") is True
