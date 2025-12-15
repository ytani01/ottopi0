#
# (c) 2025 Yoichi Tanibayashi
#

from ottopi0.__main__ import cli
from tests.conftest import assert_cli_result, cli_url_builder


class TestCliCmd:
    """`ottopi0 cmd` CLI コマンドの統合テスト。"""

    def test_cli_invocation_default(self, cli_runner, mock_cli_app):
        """デフォルト引数でコマンドを呼び出すテスト。"""
        result = cli_runner.invoke(cli, ["cmd"])

        assert_cli_result(result, expected_output_fragments=["Done."])

        # アプリがデフォルト引数で初期化されたことを検証
        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # 履歴ファイル (最初の引数) を確認
        assert args[0] is not None
        # URLがhttpプロトコルを含んでいることを確認 (2番目の引数)
        assert "http://" in args[1]

        # app.main()とapp.end()が呼び出されたことを検証
        mock_cli_app.return_value.main.assert_called_once()
        mock_cli_app.return_value.end.assert_called_once()

    def test_cli_invocation_custom(self, cli_runner, mock_cli_app):
        """カスタム引数でコマンドを呼び出すテスト。"""
        result = cli_runner.invoke(
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

        assert_cli_result(result)

        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # URL構築の確認
        expected_url = cli_url_builder("192.168.1.100", "8888", "/api/cmd")
        assert args[1] == expected_url

    def test_cli_exception_handling(self, cli_runner, mock_cli_app):
        """CLIがアプリ実行中の例外をどのように処理するかをテスト。"""
        mock_cli_app.return_value.main.side_effect = Exception("Crash!")

        result = cli_runner.invoke(cli, ["cmd"])

        assert_cli_result(
            result,
            expected_output_fragments=["Done.", "ERROR", "Exception: Crash!"],
        )

        # 例外発生時でもapp.end()が呼び出されたことを検証
        mock_cli_app.return_value.end.assert_called_once()

    def test_cli_short_options(self, cli_runner, mock_cli_app):
        """ショートオプションフラグでコマンドを呼び出すテスト。"""
        result = cli_runner.invoke(
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

        assert_cli_result(result)

        mock_cli_app.assert_called_once()
        args, kwargs = mock_cli_app.call_args

        # 履歴ファイルを確認
        assert args[0] == "/tmp/hist.txt"

        # URL構築の確認
        expected_url = cli_url_builder("localhost", "9999", "/custom/api")
        assert args[1] == expected_url
