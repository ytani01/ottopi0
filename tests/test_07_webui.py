#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest

from ottopi0.clnt.webui import WebUI


class TestWebUI:
    """ottopi0.clnt.webui.WebUI クラスの単体テスト。"""

    @pytest.fixture
    def mock_jrpc_client(self):
        """ottopi0.clnt.webui.Client をモックするフィクスチャ。"""
        with mock.patch("ottopi0.clnt.webui.Client") as MockClient:
            yield MockClient

    @pytest.fixture
    def mock_ui(self):
        """nicegui.ui をモックするフィクスチャ。"""
        with mock.patch("ottopi0.clnt.webui.ui") as MockUI:
            yield MockUI

    @pytest.fixture
    def mock_webui_internal_deps(self):
        """WebUIの内部依存関係 (ConfFile, CmdStrLib) をモックするフィクスチャ。"""
        with (
            mock.patch("ottopi0.clnt.webui.ConfFile") as MockConfFile,
            mock.patch("ottopi0.clnt.webui.CmdStrLib") as MockCmdStrLib,
        ):
            # モック設定のセットアップ
            mock_conf = MockConfFile.return_value.conf
            mock_conf.servo.funcs = {"_prefix": "PREFIX"}
            mock_conf.get.side_effect = (
                lambda k, d=None: {
                    "client": {
                        "webui": {"buttons": {"forward": "NICE_FORWARD"}}
                    }
                }
                if k == "jrpc"
                else d
            )

            # モックCmdStrLibのセットアップ
            MockCmdStrLib.return_value.expand_func.side_effect = (
                lambda x: f"EXPANDED:{x}"
            )
            yield {
                "MockConfFile": MockConfFile,
                "MockCmdStrLib": MockCmdStrLib,
                "mock_conf": mock_conf,
            }

    def test_init(self, mock_jrpc_client, mock_ui, mock_webui_internal_deps):
        """初期化とコマンドの読み込みをテスト。"""
        # モック設定のセットアップはfixtureで実行済み

        # 初期化
        app = WebUI("http://host:1234/api", 5001)

        # JrpcClientが初期化されたことを確認
        mock_jrpc_client.assert_called_with(
            "http://host:1234/api", debug=False
        )

        # コマンド展開の確認
        # "NICE_FORWARD" -> "PREFIX NICE_FORWARD" -> "EXPANDED:PREFIX NICE_FORWARD"
        assert "EXPANDED:PREFIX NICE_FORWARD" in app.cmd_forward
        # コマンドが不足している場合は空にする
        assert app.cmd_backward == ""

    def test_send_cmd(
        self, mock_jrpc_client, mock_ui, mock_webui_internal_deps
    ):
        """コマンド送信をテスト。"""
        # まずアプリを初期化する必要がある
        app = WebUI("http://host:1234/api", 5001)

        # 1. 有効なコマンドを送信
        mock_client_instance = mock_jrpc_client.return_value
        mock_client_instance.url = "http://host:1234/api"

        app.send_cmd("TEST_CMD")

        mock_client_instance.jrpc_call.assert_called_with("TEST_CMD")

        # 2. 空のコマンドを送信
        mock_client_instance.jrpc_call.reset_mock()
        app.send_cmd("")
        mock_client_instance.jrpc_call.assert_not_called()

    def test_log_message(
        self, mock_jrpc_client, mock_ui, mock_webui_internal_deps
    ):
        """UIへのロギングをテスト。"""
        app = WebUI("http://host", 5001)

        # ログコンテナのコンテキストマネージャをモック
        app.log_container = mock.MagicMock()

        app.log_message("Hello")

        app.log_container.__enter__.assert_called()
        mock_ui.label.assert_called()
        arg = mock_ui.label.call_args[0][0]
        assert "Hello" in arg

    def test_build_ui(
        self, mock_jrpc_client, mock_ui, mock_webui_internal_deps
    ):
        """UI構築呼び出しをテスト。"""
        app = WebUI("http://host", 5001)
        app.build_ui()

        # 基本的なUI要素が作成されたことを確認
        mock_ui.header.assert_called()
        mock_ui.button.assert_called()
        mock_ui.input.assert_called()
