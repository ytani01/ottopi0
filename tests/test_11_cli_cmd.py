#
# (c) 2025 Yoichi Tanibayashi
#

from click.testing import CliRunner

from ottopi0.__main__ import cli
from tests.conftest import cli_url_builder


class TestCliJrpcClntCli:
    """`ottopi0 cmd` CLI コマンドの統合テスト。"""

    def test_cli_invocation_default(self, mock_cli_app):
        """デフォルト引数でコマンドを呼び出すテスト。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["cmd"])

        assert result.exit_code == 0
        assert "Done." in result.output

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

    def test_cli_invocation_custom(self, mock_cli_app):
        """カスタム引数でコマンドを呼び出すテスト。"""
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

        # URL構築の確認
        expected_url = cli_url_builder("192.168.1.100", "8888", "/api/cmd")
        assert args[1] == expected_url

    def test_cli_exception_handling(self, mock_cli_app):
        """CLIがアプリ実行中の例外をどのように処理するかをテスト。"""
        mock_cli_app.return_value.main.side_effect = Exception("Crash!")

        runner = CliRunner()
        result = runner.invoke(cli, ["cmd"])

        assert (
            result.exit_code == 0
        )  # コマンド自体はクラッシュせず、例外をキャッチする
        # エラーがログに記録/表示されたことを確認。
        # ClickRunnerはstdoutをキャプチャ。ログはstderrに行くか、キャプチャされる。
        # CLIはfinallyブロックで"Done."を出力。
        assert "Done." in result.output

        # 例外発生時でもapp.end()が呼び出されたことを検証
        mock_cli_app.return_value.end.assert_called_once()

    def test_cli_short_options(self, mock_cli_app):
        """ショートオプションフラグでコマンドを呼び出すテスト。"""
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

        # 履歴ファイルを確認
        assert args[0] == "/tmp/hist.txt"

        # URL構築の確認
        expected_url = cli_url_builder("localhost", "9999", "/custom/api")
        assert args[1] == expected_url
