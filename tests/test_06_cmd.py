#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock

import pytest

from ottopi0.clnt.cmd import Cmd


class TestCmd:
    """JrpcClntCli (Cmd) のテストクラス。"""

    @pytest.fixture
    def mock_deps(self, mocker):
        """依存関係をモック: JrpcClient, readline, os。"""
        MockJrpcClient = mocker.patch("ottopi0.clnt.cmd.Client")
        MockReadline = mocker.patch("ottopi0.clnt.cmd.readline")
        MockOs = mocker.patch("ottopi0.clnt.cmd.os")

        yield {
            "JrpcClient": MockJrpcClient,
            "readline": MockReadline,
            "os": MockOs,
        }

    @pytest.fixture
    def cmd_app_instance(self, mock_deps):
        """Cmdアプリのインスタンスを提供するフィクスチャ。"""
        return Cmd("history_file", "http://url")

    def test_init(self, mock_deps, cmd_app_instance):
        """初期化と履歴ファイルの読み込みをテスト。"""
        assert cmd_app_instance.url == "http://url"
        mock_deps[
            "readline"
        ].read_history_file.assert_called()  # 履歴ファイルが読み込まれたことを確認

    def test_main_loop_command(self, mock_deps, cmd_app_instance, mocker):
        """メインループでのコマンド処理をテスト。"""
        # コマンドを返し、その後EOFを返すように入力をモック
        mocker.patch("builtins.input", side_effect=["cmd1", EOFError()])
        cmd_app_instance.main()

        # "cmd1"でjrpc_callが呼び出されたことを確認
        cast(
            MagicMock, cmd_app_instance.jrpcclnt.jrpc_call
        ).assert_called_with("cmd1")

    def test_main_loop_comment(self, mock_deps, cmd_app_instance, mocker):
        """メインループでのコメント除去をテスト。"""
        mocker.patch(
            "builtins.input", side_effect=["cmd # comment", EOFError()]
        )
        cmd_app_instance.main()

        # "cmd # comment" -> "cmd " (partitionはセパレータを保持するか？
        # いいえ、[0]はセパレータの前)
        # "cmd # comment".partition("#")[0] -> "cmd "
        cast(
            MagicMock, cmd_app_instance.jrpcclnt.jrpc_call
        ).assert_called_with("cmd ")

    def test_end_saves_history(self, mock_deps, cmd_app_instance):
        """endメソッドが履歴を保存することをテスト。"""
        cmd_app_instance.end()

        mock_deps["readline"].write_history_file.assert_called()

    def test_init_no_history_file(self, mock_deps, cmd_app_instance):
        """履歴ファイルがない場合 (FileNotFoundError) の初期化をテスト。"""
        mock_deps[
            "readline"
        ].read_history_file.side_effect = FileNotFoundError

        # 例外を処理し、警告をログに記録するはず
        # (get_loggerをモックすればログのアサート可能)
        # 重要なのはクラッシュしないこと
        assert cmd_app_instance.is_active

    def test_init_invalid_history_file(self, mock_deps):
        """無効な履歴ファイル (OSError) で初期化 (ファイルを削除)。"""
        mock_deps["readline"].read_history_file.side_effect = OSError

        _ = Cmd("history_file", "http://url")

        mock_deps["os"].remove.assert_called()  # ファイルを削除
