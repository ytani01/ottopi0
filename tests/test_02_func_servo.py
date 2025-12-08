#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock

import pytest

# Import the module itself to prevent circular import issues when patching
from ottopi0.jrpcsvr.func_servo import Servo


@pytest.fixture
def mock_pi0servo_classes(mocker):
    """Fixture to mock pi0servo classes StrCmdToJson and JsonRpcWorker."""
    # Patch the names in the module where they are looked up (ottopi0.func_servo)
    mock_str_cmd_to_json = mocker.patch(
        "ottopi0.jrpcsvr.func_servo.StrCmdToJson", spec=True
    )
    mock_json_rpc_worker = mocker.patch(
        "ottopi0.jrpcsvr.func_servo.JsonRpcWorker", spec=True
    )
    return mock_str_cmd_to_json, mock_json_rpc_worker


@pytest.fixture
def mock_logger(mocker):
    """Fixture to mock the get_logger function."""
    return mocker.patch(
        "ottopi0.jrpcsvr.func_servo.get_logger", return_value=MagicMock()
    )


class TestServo:
    """
    Test class for the Servo class in func_servo.py.
    """

    PINS = [-20, 26, -19, 16]

    def test_init(self, mock_pi0servo_classes, mock_logger):
        """
        Test the __init__ method of the Servo class.
        Verifies that StrCmdToJson and JsonRpcWorker are initialized correctly.
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
        """
        Test the _start method.
        Verifies that the servo worker's start method is called.
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        servo._start()

        cast(MagicMock, servo.servo.start).assert_called_once()

    def test_end(self, mock_pi0servo_classes, mock_logger):
        """
        Test the _end method.
        Verifies that the servo worker's end method is called.
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        servo._end()

        cast(MagicMock, servo.servo.end).assert_called_once()

    def test_call(self, mock_pi0servo_classes, mock_logger):
        """
        Test the call method based on the corrected understanding of the
        JSON format from the docs/str_cmd_to_json.md file.
        """
        mock_pi = MagicMock()
        servo = Servo(mock_pi, self.PINS)

        # A realistic command string with multiple commands
        cmd_str = "ms:0.5 mv:10,20,30,40"

        expected_json_list = [
            {
                "method": "move_sec",
                "params": {"sec": 0.5}
            },
            {
                "method": "move_all_angles_sync",
                "params": {"angles": [10, 20, 30, 40]}
            }
        ]

        expected_return_value = "jrpc_worker_return_value"

        # Mock the return values of the instance methods
        cast(
            MagicMock, servo.parser.cmdstr_to_jsonlist
        ).return_value = expected_json_list
        cast(MagicMock, servo.servo.call).return_value = expected_return_value

        actual_return_value = servo.call(cmd_str)

        # Assert that the parser was called correctly
        cast(
            MagicMock, servo.parser.cmdstr_to_jsonlist
        ).assert_called_once_with(cmd_str)

        # Assert that the jrpc worker was called with the parser's output
        cast(
            MagicMock, servo.servo.call
        ).assert_called_once_with(expected_json_list)

        # Assert that the method returns the value from the jrpc worker
        assert actual_return_value == expected_return_value
