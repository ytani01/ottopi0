#
# (c) 2025 Yoichi Tanibayashi
#
import json
import requests

from  pibtinput import PiBtInput

from .utils.mylogger import errmsg, get_logger


class RpcClntBt:
    """RPC Client: BlueTooth."""

    KEY_BIND = {
        "KEY_C": "ms:.05 mr:5,0,0,0",
        "KEY_D": "ms:.05 mr:-5,0,0,0",

        "KEY_E": "ms:.05 mr:0,5,0,0",
        "KEY_F": "ms:.05 mr:0,-5,0,0",

        "KEY_H": "ms:.05 mr:0,0,0,5",
        "KEY_J": "ms:.05 mr:0,0,0,-5",

        "KEY_G": "ms:.05 mr:0,0,5,0",
        "KEY_I": "ms:.05 mr:0,0,-5,0",
    }

    def __init__(self, btdev_keyword, url, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("btdev_keyword=%s, url=%s", btdev_keyword, url)

        self.bt_input = PiBtInput(debug=self.__debug)
        self.url = url

        self.prev_onkeys: dict[str, int] = {}

        self.input_dev = self.bt_input.search_input_devs(btdev_keyword)
        self.__log.debug("input_dev=%s", self.input_dev)

        self.rpc_id = 0

    def main(self):
        """Main."""
        self.__log.debug("")

        self.bt_input.read_loop(self.input_dev[0], self.cb_ev)

    def rpc_call(self, cmd_str: str):
        """JSON-RPC call."""
        self.__log.debug("cmd_str=%s", cmd_str)

        self.rpc_id += 1
        
        payload = {
            "jsonrpc": 2.0,
            "id": self.rpc_id,
            "method": "servo.call",
            "params": [cmd_str]
        }
        self.__log.debug("payload=%s", payload)

        response = requests.post(self.url, json=payload)
        self.__log.debug("response=%s", response)

        result = response.json()

        if "result" in result:
            self.__log.info("result: %s", result['result'])
        elif "error" in result:
            self.__log.info("error: %s", result['error'])

    def cb_ev(self, key_name, key_state, onkeys):
        """Event Callback."""
        self.__log.debug(
            "key_name=%s,key_state=%s,onkeys=%s", key_name, key_state, onkeys
        )

        if onkeys == self.prev_onkeys:
            return True

        self.prev_onkeys = onkeys.copy()

        if key_state == PiBtInput.KEY["up"]:
            self.rpc_call("ca")
            return True

        print(key_name)

        if key_name == "KEY_S":
            self.__log.info("END")
            return False

        if key_name not in self.KEY_BIND:
            return True

        self.rpc_call(self.KEY_BIND[key_name])

        return True

    def end(self):
        """End."""
        self.__log.debug("")
