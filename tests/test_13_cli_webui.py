#
# (c) 2025 Yoichi Tanibayashi
#

from ottopi0.__main__ import cli
from tests.conftest import assert_cli_result, cli_url_builder


class TestCliWebUI:
    """`ottopi0 webui` CLI コマンドの統合テスト。"""

    def test_cli_invocation_default(self, cli_runner, mock_webui_app):
        """デフォルト引数でコマンドを呼び出すテスト。"""
        result = cli_runner.invoke(cli, ["webui"])

        assert_cli_result(result, expected_output_fragments=["Done."])

        # アプリがデフォルト引数で初期化されたことを検証
        mock_webui_app.assert_called_once()
        args, kwargs = mock_webui_app.call_args

        # URLがhttpプロトコルを含んでいることを確認
        assert "http://" in args[0]
        # webui_portキーワード引数が渡されたことを確認
        assert "webui_port" in kwargs

        # app.run()が呼び出されたことを検証
        mock_webui_app.return_value.run.assert_called_once()

    def test_cli_invocation_custom(self, cli_runner, mock_webui_app):
        """カスタム引数でコマンドを呼び出すテスト。"""
        result = cli_runner.invoke(
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

        assert_cli_result(result)

        mock_webui_app.assert_called_once()
        args, kwargs = mock_webui_app.call_args

        # URL構築の確認
        expected_url = cli_url_builder("192.168.1.100", "8888", "/api/cmd")
        assert args[0] == expected_url

        # WebUIポートの確認
        assert kwargs.get("webui_port") == 9000

    def test_cli_exception_handling(self, cli_runner, mock_webui_app):
        """CLIがアプリ実行中の例外をどのように処理するかをテスト。"""
        mock_webui_app.return_value.run.side_effect = Exception("Crash!")

        result = cli_runner.invoke(cli, ["webui"])

        assert_cli_result(
            result,
            expected_output_fragments=["ERROR", "Exception: Crash!", "Done."],
        )
