#
# (c) 2025 Yoichi Tanibayashi
#
import requests
from pibtinput import PiBtInput

from . import Config
from .utils.mylogger import errmsg, get_logger


class RpcClntBt:
    """RPC Client: BlueTooth."""

    def __init__(self, btdev_keyword, url, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("btdev_keyword=%s, url=%s", btdev_keyword, url)

        self.bt_input = PiBtInput(debug=False)
        self.url = url

        self.prev_onkeys: dict[str, int] = {}

        self.rpc_id = 0

        self.is_active = False

        self.input_dev = self.bt_input.search_input_devs(btdev_keyword)
        self.__log.debug("input_dev=%s", self.input_dev)
        if not self.input_dev:
            self.__log.error("No input device")
        else:
            self.is_active = True

        self.conf = Config.rpcclnt_bt
        self.keys = self.conf.get("keys")
        self.mr_keys = self.conf.get("mr_keys")
        self.__log.debug("keys=%s, mr_keys=%s", self.keys, self.mr_keys)

    def main(self):
        """Main."""
        self.__log.debug("")

        while self.is_active:
            try:
                self.bt_input.read_loop(self.input_dev[0], self.cb_ev)
            except Exception as e:
                self.__log.error(errmsg(e))

    def rpc_call(self, cmd_str: str):
        """JSON-RPC call."""
        self.__log.debug("cmd_str=%s", cmd_str)

        self.rpc_id += 1

        payload = {
            "jsonrpc": 2.0,
            "id": self.rpc_id,
            "method": "servo.call",
            "params": [cmd_str],
        }
        self.__log.debug("payload=%s", payload)

        response = requests.post(self.url, json=payload)
        self.__log.debug("response=%s", response)

        result = response.json()

        if "result" in result:
            self.__log.info("result: %s", result["result"])
        elif "error" in result:
            self.__log.info("error: %s", result["error"])

    def cb_ev(self, key_name, key_state, onkeys):
        """Event Callback."""
        self.__log.debug(
            "key_name=%a,key_state=%s,onkeys=%s", key_name, key_state, onkeys
        )

        if onkeys == self.prev_onkeys:
            return True

        self.prev_onkeys = onkeys.copy()

        if key_state == PiBtInput.KEY["up"]:
            # キーを離したらコマンドをキャンセルして停止
            #self.rpc_call("ca")
            return True

        print(key_name)

        if key_name in self.keys:
            # normal key
            cmd_str = self.conf.get("prefix") + " " + self.keys.get(key_name)
            self.__log.debug("cmd_str=%a", cmd_str)
            self.rpc_call(cmd_str)
            return True

        # "mr" ?
        angle_diffs = [0, 0, 0, 0]
        for key in onkeys:
            if key in self.mr_keys:
                ad = self.mr_keys.get(key)
                angle_diffs = [a + b for a, b in zip(angle_diffs, ad)]
        self.__log.debug("angle_diffs=%s", angle_diffs)

        if angle_diffs == [0, 0, 0, 0]:
            # not "mr"
            return True

        # "mr" !
        cmd_str = self.conf.get("mr_prefix")
        cmd_str += ",".join(map(str, angle_diffs))
        self.__log.debug("cmd_str=%a", cmd_str)

        self.rpc_call(cmd_str)
        return True

    def end(self):
        """End."""
        self.__log.debug("")
