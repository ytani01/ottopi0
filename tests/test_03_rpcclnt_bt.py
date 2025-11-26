#
# (c) 2025 Yoichi Tanibayashi
#
from unittest.mock import MagicMock

import pytest

from ottopi0.rpcclnt_bt import RpcClntBt


@pytest.fixture
def mock_pibtinput(mocker):
    """Fixture to mock pibtinput.PiBtInput."""
    mock = mocker.patch("ottopi0.rpcclnt_bt.PiBtInput", spec=True)
    # Configure the KEY attribute on the mock class
    mock.KEY = {"up": 0, "down": 1, "hold": 2}
    return mock


@pytest.fixture
def mock_requests(mocker):
    """Fixture to mock requests.post."""
    return mocker.patch("ottopi0.rpcclnt_bt.requests.post")


@pytest.fixture
def mock_logger(mocker):
    """Fixture to mock the get_logger function."""
    return mocker.patch(
        "ottopi0.rpcclnt_bt.get_logger", return_value=MagicMock()
    )


@pytest.fixture
def mock_config(mocker):
    """Fixture to mock the Config object."""
    mock_conf_obj = {
        "prefix": "ms:0.4",
        "mr_prefix": "ms:0.3 st:10 mr:",
        "keys": {
            "KEY_A": "mv:10,10,10,10",
            "KEY_B": "ca",
        },
        "mr_keys": {
            "KEY_C": [5, 0, 0, 0],
            "KEY_D": [0, -5, 0, 0],
        },
    }
    mock = mocker.patch("ottopi0.rpcclnt_bt.Config")
    mock.rpcclnt_bt = mock_conf_obj
    return mock


class TestRpcClntBt:
    """Test class for RpcClntBt."""

    BTDEV_KEYWORD = ["test_dev"]
    URL = "http://localhost:8000/api"

    def test_init_device_found(
        self, mock_pibtinput, mock_config, mock_logger
    ):
        """Test initialization when a Bluetooth device is found."""
        mock_pibtinput_instance = mock_pibtinput.return_value
        mock_pibtinput_instance.search_input_devs.return_value = [
            "dummy_device"
        ]

        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)

        mock_pibtinput.assert_called_once_with(debug=False)
        mock_pibtinput_instance.search_input_devs.assert_called_once_with(
            self.BTDEV_KEYWORD
        )
        assert client.is_active is True
        assert client.conf == mock_config.rpcclnt_bt

    def test_init_device_not_found(
        self, mock_pibtinput, mock_config, mock_logger
    ):
        """Test initialization when no Bluetooth device is found."""
        mock_pibtinput_instance = mock_pibtinput.return_value
        mock_pibtinput_instance.search_input_devs.return_value = []

        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)

        assert client.is_active is False

    def test_main_loop(self, mock_pibtinput, mock_config, mock_logger):
        """Test the main loop starts and can be exited."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        client.is_active = True

        # Make read_loop raise an exception to exit the while loop
        client.bt_input.read_loop.side_effect = [None, KeyboardInterrupt]

        with pytest.raises(KeyboardInterrupt):
            client.main()

        assert client.bt_input.read_loop.call_count == 2
        client.bt_input.read_loop.assert_called_with(
            client.input_dev[0], client.cb_ev
        )

    def test_rpc_call(
        self, mock_pibtinput, mock_config, mock_requests, mock_logger
    ):
        """Test the rpc_call method."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        cmd_str = "test_command"

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_requests.return_value = mock_response

        client.rpc_call(cmd_str)

        expected_payload = {
            "jsonrpc": 2.0,
            "id": 1,  # First call
            "method": "servo.call",
            "params": [cmd_str],
        }
        mock_requests.assert_called_once_with(self.URL, json=expected_payload)

    def test_cb_ev_normal_key(self, mock_pibtinput, mock_config, mock_logger):
        """Test event callback for a normal key press."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        client.rpc_call = MagicMock()

        key_name = "KEY_A"
        key_state = mock_pibtinput.KEY["down"]
        onkeys = {key_name: 1}

        client.cb_ev(key_name, key_state, onkeys)

        expected_cmd_str = "ms:0.4 mv:10,10,10,10"
        client.rpc_call.assert_called_once_with(expected_cmd_str)

    def test_cb_ev_mr_key(self, mock_pibtinput, mock_config, mock_logger):
        """Test event callback for a 'move relative' key press."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        client.rpc_call = MagicMock()

        key_name = "KEY_C"
        key_state = mock_pibtinput.KEY["down"]
        onkeys = {key_name: 1, "KEY_D": 1}

        client.cb_ev(key_name, key_state, onkeys)

        # angle_diffs = [5,0,0,0] + [0,-5,0,0] = [5,-5,0,0]
        expected_cmd_str = "ms:0.3 st:10 mr:5,-5,0,0"
        client.rpc_call.assert_called_once_with(expected_cmd_str)

    def test_cb_ev_key_up(self, mock_pibtinput, mock_config, mock_logger):
        """Test event callback for a key release."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        client.rpc_call = MagicMock()

        key_name = "KEY_A"
        key_state = mock_pibtinput.KEY["up"]
        onkeys = {}

        result = client.cb_ev(key_name, key_state, onkeys)

        # The logic for 'up' state currently does nothing but return
        client.rpc_call.assert_not_called()
        assert result is True

    def test_cb_ev_no_change(self, mock_pibtinput, mock_config, mock_logger):
        """Test event callback when key state has not changed."""
        client = RpcClntBt(self.BTDEV_KEYWORD, self.URL)
        client.rpc_call = MagicMock()

        onkeys = {"KEY_A": 1}
        client.prev_onkeys = onkeys.copy()

        result = client.cb_ev("KEY_A", mock_pibtinput.KEY["down"], onkeys)

        client.rpc_call.assert_not_called()
        assert result is True
