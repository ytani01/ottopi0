#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock

import pytest

# パッチ適用時の循環インポートの問題を防ぐため、モジュール自体をインポート
from ottopi0.svr.func_servo import Servo


@pytest.fixture
def mock_pi0servo_classes(mocker):
    """pi0servoクラスStrCmdToJsonとJsonRpcWorkerをモックするフィクスチャ。"""
    # 検索されるモジュール (ottopi0.func_servo) 内の名前をパッチする
    mock_str_cmd_to_json = mocker.patch(
        "ottopi0.svr.func_servo.StrCmdToJson", spec=True
    )
    mock_json_rpc_worker = mocker.patch(
        "ottopi0.svr.func_servo.JsonRpcWorker", spec=True
    )
    return mock_str_cmd_to_json, mock_json_rpc_worker


@pytest.fixture
def mock_logger(mocker):
    """get_logger関数をモックするフィクスチャ。"""
    return mocker.patch(
        "ottopi0.svr.func_servo.get_logger", return_value=MagicMock()
    )


class TestServo:
    """func_servo.py内のServoクラスのテストクラス。"""

    PINS = [-20, 26, -19, 16]

    def test_init(self, mock_pi0servo_classes, mock_logger):
        """Servoクラスの__init__メソッドをテスト。
        StrCmdToJsonとJsonRpcWorkerが正しく初期化されていることを検証する。
        """
        StrCmdToJson, JsonRpcWorker = mock_pi0servo_classes
        mock_pi = MagicMock()
        debug_mode1 = True
        debug_mode2 = False

        servo = Servo(mock_pi, self.PINS, debug=debug_mode1)

        StrCmdToJson.assert_called_once_with(debug=debug_mode1)
        JsonRpcWorker.assert_called_once_with(
            mock_pi, self.PINS, flag_verbose=True, debug=debug_mode2
        )
        assert servo.pi == mock_pi
        assert servo.pins == self.PINS

    def test_start(self, mock_pi0servo_classes, mock_logger):
        """_startメソッドをテスト。
        サーボワーカーのstartメソッドが呼び出されることを検証する。
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        servo._start()

        cast(MagicMock, servo.servo.start).assert_called_once()

    def test_end(self, mock_pi0servo_classes, mock_logger):
        """_endメソッドをテスト。
        サーボワーカーのendメソッドが呼び出されることを検証する。
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        servo._end()

        cast(MagicMock, servo.servo.end).assert_called_once()

    def test_call(self, mock_pi0servo_classes, mock_logger):
        """docs/str_cmd_to_json.mdファイルからのJSONフォーマットの
        修正された理解に基づいてcallメソッドをテスト。
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        # 複数のコマンドを含む現実的なコマンド文字列
        cmd_str = "ms:0.5 mv:10,20,30,40"

        expected_json_list = [
            {"method": "move_sec", "params": {"sec": 0.5}},
            {
                "method": "move_all_angles_sync",
                "params": {"angles": [10, 20, 30, 40]},
            },
        ]

        expected_return_value = "jrpc_worker_return_value"

        # インスタンスメソッドの戻り値をモック
        cast(
            MagicMock, servo.parser.cmdstr_to_jsonlist
        ).return_value = expected_json_list
        cast(MagicMock, servo.servo.call).return_value = expected_return_value

        actual_return_value = servo.call(cmd_str)

        # パーサーが正しく呼び出されたことをアサート
        cast(
            MagicMock, servo.parser.cmdstr_to_jsonlist
        ).assert_called_once_with(cmd_str)

        # jrpcワーカーがパーサーの出力で呼び出されたことをアサート
        cast(MagicMock, servo.servo.call).assert_called_once_with(
            expected_json_list
        )

        # メソッドがjrpcワーカーからの値を返すことをアサート
        assert actual_return_value == expected_return_value
