#
# (c) 2025 Yoichi Tanibayashi
#
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 重要: テスト対象モジュールはモック設定後にインポートする必要がある
# モックがそのモジュールのトップレベルコードに影響を与える必要がある場合。
# この場合、jrpcsvrをインポートする前に依存関係をパッチする。


@pytest.fixture(scope="function")
def mock_env_and_deps(mocker):  # Add mocker as an argument
    """jrpcsvr.pyの外部依存関係を全てモックする包括的なフィクスチャ。
    インポート前に実行される。モジュールごとに一度だけ実行。
    """
    # 環境変数をモック (mocker.patch.dictを使用)
    mocker.patch.dict(
        os.environ, {"ottopi0_DEBUG": "1", "ottopi0_SERVO_PINS": "20-,26"}
    )

    # ライブラリをモック
    patcher_pigpio = patch("ottopi0.svr.svr.pigpio", spec=True)
    patcher_logger = patch(
        "ottopi0.svr.svr.get_logger", return_value=MagicMock()
    )
    patcher_servo = patch("ottopi0.svr.svr.Servo", spec=True)
    patcher_calc = patch("ottopi0.svr.svr.Calc", spec=True)
    patcher_dispatcher = patch("ottopi0.svr.svr.dispatcher", spec=True)

    # 全てのパッチャーを開始
    mock_pigpio = patcher_pigpio.start()
    mock_logger = patcher_logger.start()
    mock_servo = patcher_servo.start()
    mock_calc = patcher_calc.start()
    mock_dispatcher = patcher_dispatcher.start()

    yield {
        "pigpio": mock_pigpio,
        "logger": mock_logger,
        "Servo": mock_servo,
        "Calc": mock_calc,
        "dispatcher": mock_dispatcher,
    }

    # 全てのパッチャーを逆順に停止
    patcher_dispatcher.stop()
    patcher_calc.stop()
    patcher_servo.stop()
    patcher_logger.stop()
    patcher_pigpio.stop()


# This fixture depends on the module-level setup fixture
@pytest.fixture
def client(mock_env_and_deps):
    """FastAPIアプリのTestClientインスタンスを提供する。
    ここでライフスパンマネージャーがトリガーされる。
    """
    # 依存関係がモックされたので、ここでモジュールをインポートする
    from ottopi0.svr.svr import api

    with TestClient(api) as test_client:
        yield test_client


class TestJrpcsvr:
    """jrpcsvr.pyのテストクラス。"""

    def test_lifespan_startup(self, client, mock_env_and_deps):
        """ライフスパンマネージャーの起動部分をテスト。
        `client`フィクスチャがすでに起動シーケンスをトリガーするため、
        このテストは本体で何もする必要はない。副作用をアサートするだけ。
        """
        mock_pigpio = mock_env_and_deps["pigpio"]
        MockServo = mock_env_and_deps["Servo"]
        MockCalc = mock_env_and_deps["Calc"]
        mock_dispatcher = mock_env_and_deps["dispatcher"]

        # 起動時のアサート
        mock_pigpio.pi.assert_called_once()
        mock_dispatcher.add_class.assert_called_once_with(MockCalc)

        expected_pins = [-20, 26]
        MockServo.assert_called_once_with(
            mock_pigpio.pi.return_value,
            expected_pins,
            debug=True,
        )

        mock_servo_instance = MockServo.return_value
        mock_servo_instance._start.assert_called_once()
        mock_dispatcher.add_object.assert_called_once_with(
            mock_servo_instance
        )

    def test_lifespan_shutdown(self, mock_env_and_deps):
        """ライフスパンマネージャーのシャットダウン部分をテスト。
        シャットダウンを制御するために、このテスト内でクライアントインスタンスを作成する。
        """
        from ottopi0.svr.svr import api

        # 'with'ブロックは起動とシャットダウンをトリガーする
        with TestClient(api):
            pass

        mock_pigpio_instance = mock_env_and_deps["pigpio"].pi.return_value
        mock_servo_instance = mock_env_and_deps["Servo"].return_value

        # シャットダウン時のアサート
        mock_servo_instance._end.assert_called_once()
        mock_pigpio_instance.stop.assert_called_once()

    @patch("ottopi0.svr.svr.JSONRPCResponseManager.handle")
    def test_handle_req_success(self, mock_handle, client, mock_env_and_deps):
        """成功したJSON-RPC応答で/apiエンドポイントをテスト。"""
        json_payload = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        mock_response = MagicMock()
        mock_response.data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        mock_handle.return_value = mock_response

        response = client.post("/api", json=json_payload)

        assert response.status_code == 200
        assert response.json() == mock_response.data

        # 生の文字列ボディとディスパッチャでハンドルが呼び出されたことを検証
        mock_handle.assert_called_once_with(
            '{"jsonrpc":"2.0","id":1,"method":"test"}',
            mock_env_and_deps["dispatcher"],
        )

    @patch("ottopi0.svr.svr.JSONRPCResponseManager.handle")
    def test_handle_req_no_response(self, mock_handle, client):
        """応答マネージャーが何も返さない場合の/apiエンドポイントをテスト。"""
        json_payload = {"jsonrpc": "2.0", "id": 1, "method": "notify"}
        # 通知用

        response = client.post("/api", json=json_payload)

        assert response.status_code == 200
        assert response.json() == {}
