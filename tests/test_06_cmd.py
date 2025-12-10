#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from ottopi0.clnt.cmd import Cmd


class TestJrpcClntCli:
    """JrpcClntCliのテストクラス。"""

    @pytest.fixture
    def mock_deps(self):
        """依存関係をモック: JrpcClient, readline, os。"""
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
        """初期化と履歴ファイルの読み込みをテスト。"""
        cli_obj = Cmd("history_file", "http://url")

        assert cli_obj.url == "http://url"
        mock_deps[
            "readline"
        ].read_history_file.assert_called()  # 履歴ファイルが読み込まれたことを確認

    def test_main_loop_command(self, mock_deps):
        """メインループでのコマンド処理をテスト。"""
        cli_obj = Cmd("history_file", "http://url")

        # コマンドを返し、その後EOFを返すように入力をモック
        # (Ctrl-DをシミュレートするEOFErrorを発生させるか、ループを終了させるか？)
        # コードはEOFErrorをキャッチして中断する。
        with patch("builtins.input", side_effect=["cmd1", EOFError()]):
            cli_obj.main()

        # "cmd1"でjrpc_callが呼び出されたことを確認
        cast(MagicMock, cli_obj.jrpcclnt.jrpc_call).assert_called_with("cmd1")

    def test_main_loop_comment(self, mock_deps):
        """メインループでのコメント除去をテスト。"""
        cli_obj = Cmd("history_file", "http://url")

        with patch(
            "builtins.input", side_effect=["cmd # comment", EOFError()]
        ):
            cli_obj.main()

        # "cmd # comment" -> "cmd " (partitionはセパレータを保持するか？
        # いいえ、[0]はセパレータの前)
        # "cmd # comment".partition("#")[0] -> "cmd "
        cast(MagicMock, cli_obj.jrpcclnt.jrpc_call).assert_called_with("cmd ")

    def test_end_saves_history(self, mock_deps):
        """endメソッドが履歴を保存することをテスト。"""
        cli_obj = Cmd("history_file", "http://url")
        cli_obj.end()

        mock_deps["readline"].write_history_file.assert_called()

    def test_init_no_history_file(self, mock_deps):
        """履歴ファイルがない場合 (FileNotFoundError) の初期化をテスト。"""
        mock_deps[
            "readline"
        ].read_history_file.side_effect = FileNotFoundError

        cli_obj = Cmd("history_file", "http://url")
        # 例外を処理し、警告をログに記録するはず
        # (get_loggerをモックすればログのアサート可能)
        # 重要なのはクラッシュしないこと
        assert cli_obj.is_active

    def test_init_invalid_history_file(self, mock_deps):
        """無効な履歴ファイル (OSError) で初期化 (ファイルを削除)。"""
        mock_deps["readline"].read_history_file.side_effect = OSError

        _ = Cmd("history_file", "http://url")

        mock_deps["os"].remove.assert_called()  # ファイルを削除
