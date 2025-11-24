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

        self.key_bind = {}
        self.__log.debug("keys:%s", Config.rpcclnt_bt.get("keys"))
        for b in Config.rpcclnt_bt.get("keys"):
            key, cmd = b.split(":", 1)
            self.key_bind[key] = cmd.strip()
        self.__log.debug("key_bind=%s", self.key_bind)

        print("KEY_S" in self.key_bind)

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
            self.rpc_call("ca")
            return True

        print(key_name)

        angle_diffs = [0, 0, 0, 0]
        for key in onkeys:
            if key in self.key_bind:
                cmd = self.key_bind[key]
                if cmd.startswith("mR"):
                    params = cmd.split(",")
                    angle_diffs[int(params[1])] = int(params[2])
                else:
                    self.rpc_call(cmd)

        if angle_diffs != [0, 0, 0, 0]:
            self.__log.debug("angle_diffs=%s", angle_diffs)
            cmd_str = "ms:0.2 st:10 mr:" + ",".join(map(str, angle_diffs))
            self.rpc_call(cmd_str)

        return True

    def end(self):
        """End."""
        self.__log.debug("")
