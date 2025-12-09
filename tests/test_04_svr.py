#
# (c) 2025 Yoichi Tanibayashi
#
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Important: The module under test must be imported AFTER setting up mocks
# if mocks need to affect top-level code in that module.
# In this case, we patch dependencies before importing jrpcsvr.


@pytest.fixture(scope="function")
def mock_env_and_deps():
    """
    A comprehensive fixture to mock all external dependencies for jrpcsvr.py
    before it is imported. This runs only once per module.
    """
    # Mock environment variables
    os.environ["ottopi0_DEBUG"] = "1"
    os.environ["ottopi0_SERVO_PINS"] = "20-,26"

    # Mock libraries
    patcher_pigpio = patch("ottopi0.svr.svr.pigpio", spec=True)
    patcher_logger = patch(
        "ottopi0.svr.svr.get_logger", return_value=MagicMock()
    )
    patcher_servo = patch("ottopi0.svr.svr.Servo", spec=True)
    patcher_calc = patch("ottopi0.svr.svr.Calc", spec=True)
    patcher_dispatcher = patch("ottopi0.svr.svr.dispatcher", spec=True)

    # Start all patchers
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

    # Stop all patchers in reverse order
    patcher_dispatcher.stop()
    patcher_calc.stop()
    patcher_servo.stop()
    patcher_logger.stop()
    patcher_pigpio.stop()

    # Clean up environment variables
    del os.environ["ottopi0_DEBUG"]
    del os.environ["ottopi0_SERVO_PINS"]


# This fixture depends on the module-level setup fixture
@pytest.fixture
def client(mock_env_and_deps):
    """
    Provides a TestClient instance for the FastAPI app.
    The lifespan manager is triggered here.
    """
    # Import the module now that dependencies are mocked
    from ottopi0.svr.svr import api

    with TestClient(api) as test_client:
        yield test_client


class TestJrpcsvr:
    """Test class for jrpcsvr.py."""

    def test_lifespan_startup(self, client, mock_env_and_deps):
        """
        Tests the startup part of the lifespan manager.
        This test doesn't need to do anything in the body because the `client`
        fixture already triggers the startup sequence. We just need to assert
        the side effects.
        """
        mock_pigpio = mock_env_and_deps["pigpio"]
        MockServo = mock_env_and_deps["Servo"]
        MockCalc = mock_env_and_deps["Calc"]
        mock_dispatcher = mock_env_and_deps["dispatcher"]

        # Assertions for startup
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
        """
        Tests the shutdown part of the lifespan manager.
        We create a client instance within this test to control the shutdown.
        """
        from ottopi0.svr.svr import api

        # The 'with' block triggers startup and shutdown
        with TestClient(api):
            pass

        mock_pigpio_instance = mock_env_and_deps["pigpio"].pi.return_value
        mock_servo_instance = mock_env_and_deps["Servo"].return_value

        # Assertions for shutdown
        mock_servo_instance._end.assert_called_once()
        mock_pigpio_instance.stop.assert_called_once()

    @patch("ottopi0.svr.svr.JSONRPCResponseManager.handle")
    def test_handle_req_success(self, mock_handle, client, mock_env_and_deps):
        """
        Tests the /api endpoint with a successful JSON-RPC response.
        """
        json_payload = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        mock_response = MagicMock()
        mock_response.data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        mock_handle.return_value = mock_response

        response = client.post("/api", json=json_payload)

        assert response.status_code == 200
        assert response.json() == mock_response.data

        # Verify handle was called with the raw string body and the dispatcher
        mock_handle.assert_called_once_with(
            '{"jsonrpc":"2.0","id":1,"method":"test"}',
            mock_env_and_deps["dispatcher"],
        )

    @patch("ottopi0.svr.svr.JSONRPCResponseManager.handle")
    def test_handle_req_no_response(self, mock_handle, client):
        """
        Tests the /api endpoint when the response manager returns nothing.
        """
        json_payload = {"jsonrpc": "2.0", "id": 1, "method": "notify"}
        mock_handle.return_value = None  # For notifications

        response = client.post("/api", json=json_payload)

        assert response.status_code == 200
        assert response.json() == {}
