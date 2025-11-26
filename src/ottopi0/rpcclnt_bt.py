#
# (c) 2025 Yoichi Tanibayashi
#
import time

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

        self.btdev_keyword = btdev_keyword
        self.url = url

        # initialize vars
        self.prev_onkeys: dict[str, int] = {}
        self.rpc_id = 0
        self.is_active = False

        # init BlueTooth
        self.bt_input = PiBtInput(debug=False)
        self.input_dev = self.bt_input.search_input_devs(self.btdev_keyword)
        self.__log.debug("input_dev=%s", self.input_dev)
        if not self.input_dev:
            self.__log.error("No input device")
        else:
            self.is_active = True

        # load config files
        self.funcs = Config.funcs
        self.__log.debug("funcs=%s", self.funcs)

        self.conf = Config.rpcclnt_bt
        self.keys = self.conf.get("keys")
        self.mr_keys = self.conf.get("mr_keys")
        self.__log.debug("keys=%s, mr_keys=%s", self.keys, self.mr_keys)

        # keymap
        self.keymap: dict[str, str] = self.mk_keymap(
            self.funcs, self.keys, self.funcs.get("_prefix")
        )
        self.__log.debug("keymap=%s", self.keymap)

    def mk_keymap(self, funcs, keys, cmd_prefix) -> dict[str, str]:
        """Make Key binds."""
        self.__log.debug("funcs=%s", funcs)
        self.__log.debug("keys=%s", keys)
        self.__log.debug("cmd_prefix=%s", cmd_prefix)

        _keymap = {}
        for k in keys:
            _fname = keys.get(k)
            if not _fname:
                self.__log.error("%s: no such key definition", k)
                continue
            _cmdline = funcs.get(_fname)

            if not _cmdline:
                self.__log.error("%s: no such function definition", _fname)
                continue

            _keymap[k] = cmd_prefix + " " + _cmdline

        return _keymap

    def main(self):
        """Main."""
        self.__log.debug("")

        while self.is_active:
            try:
                self.bt_input.read_loop(self.input_dev[0], self.cb_ev)
            except requests.exceptions.ConnectionError as e:
                self.__log.error(errmsg(e))
            except OSError as e:
                # BlueTooth is lost ?
                self.__log.error(errmsg(e))
                time.sleep(3)
                self.input_dev = self.bt_input.search_input_devs(
                    self.btdev_keyword
                )
                self.__log.error("input_dev=%s", self.input_dev)
            except IndexError as e:
                # BlueTooth is lost ?
                self.__log.error(errmsg(e))
                time.sleep(1)
                self.input_dev = self.bt_input.search_input_devs(
                    self.btdev_keyword
                )
                self.__log.error("input_dev=%s", self.input_dev)

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

        try:
            response = requests.post(self.url, json=payload)
        except requests.exceptions.ConnectionError as e:
            self.__log.error(errmsg(e))
            return

        self.__log.debug("response=%s", response)

        result = response.json()

        if "result" in result:
            self.__log.debug("result: %s", result["result"])
        elif "error" in result:
            self.__log.debug("error: %s", result["error"])

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
            # self.rpc_call("ca")
            return True

        if key_state == PiBtInput.KEY["hold"]:
            return True

        self.__log.debug("key_name=%a", key_name)

        if key_name in self.keymap.keys():
            # normal key
            _cmd_str = self.keymap.get(key_name)
            self.__log.debug("_cmd_str=%a", _cmd_str)

            if _cmd_str:
                self.rpc_call(_cmd_str)

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
