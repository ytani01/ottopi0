#
# (c) 2025 Yoichi Tanibayashi
#
import time

import requests
from pibtinput import PiBtInput

from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import errmsg, get_logger
from .jrpcclnt import JrpcClient


class JrpcClntBt:
    """JSON-RPC Client: BlueTooth."""

    CHR_MULTI_KEYS = "-"

    def __init__(self, btdev_keyword, url, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("btdev_keyword=%s, url=%s", btdev_keyword, url)

        self.btdev_keyword = btdev_keyword
        self.url = url

        self.cslib = CmdStrLib(debug=self.__debug)
        self.jrpc_clnt = JrpcClient(self.url, debug=self.__debug)

        # initialize vars
        self.prev_onkeys: dict[str, int] = {}
        self.jrpc_id = 0
        self.is_active = True

        # init BlueTooth
        self.bt_input = PiBtInput(debug=False)
        self.input_dev = self.bt_input.search_input_devs(self.btdev_keyword)
        self.__log.debug("input_dev=%s", self.input_dev)

        # load config files
        self.conf = ConfFile(debug=self.__debug).conf

        self.funcs = self.conf.servo.funcs
        self.__log.debug("funcs=%s", self.funcs)

        self.cmd_prefix = self.funcs.get("_prefix")
        self.__log.debug("cmd_prefix=%a", self.cmd_prefix)

        self.btconf = self.conf.jrpc.client.bluetooth
        self.keys = self.btconf.get("keys")
        self.mr_keys = self.btconf.get("mr_keys")
        self.__log.debug("keys=%s, mr_keys=%s", self.keys, self.mr_keys)

        # keymap
        self.keymap: dict[str, str] = self.mk_keymap(self.keys)
        self.__log.debug("keymap=%s", self.keymap)

    def mk_keymap(self, keys) -> dict[str, str]:
        """Make Key binds."""
        self.__log.debug("keys=%s", keys)

        _keymap = {}
        for k in keys:
            _cmdline = keys.get(k)
            self.__log.debug("_cmdline=%a", _cmdline)

            # Support chord (multiple keys)
            if self.CHR_MULTI_KEYS in k:
                # normalize key name: "KEY_B-KEY_A" -> "KEY_A-KEY_B"
                k = self.CHR_MULTI_KEYS.join(
                    sorted(k.split(self.CHR_MULTI_KEYS))
                )
                self.__log.debug("normalized key=%a", k)

            _cmdline = self.cslib.expand_func(f"{self.cmd_prefix} {_cmdline}")
            self.__log.debug("_cmdline=%a", _cmdline)

            _keymap[k] = _cmdline

        return _keymap

    def cb_ev(self, key_name, key_state, onkeys):
        """Event Callback."""

        # if onkeys == self.prev_onkeys:
        #     return True

        self.prev_onkeys = onkeys.copy()

        if key_state == PiBtInput.KEY["up"]:
            # キーを離したらコマンドをキャンセルして停止？
            # self.jrpc_call("ca")
            return True

        if key_state == PiBtInput.KEY["hold"]:
            # リピートは無視
            return True

        self.__log.debug(
            "key_name=%a,key_state=%s,onkeys=%s", key_name, key_state, onkeys
        )

        #
        # "down"
        #
        self.__log.debug("key_name=%a", key_name)

        #
        # check chord (multiple keys)
        #
        _current_keys = sorted(onkeys.keys())
        _current_combo = self.CHR_MULTI_KEYS.join(_current_keys)
        self.__log.debug("_current_combo=%a", _current_combo)

        _cmd_str = self.keymap.get(_current_combo)
        self.__log.debug("%s>_cmd_str=%s", _current_combo, _cmd_str)

        # # 複数押しがマッチしなければ、単押しをチェック
        # if not _cmd_str:
        #     # check single key (legacy)
        #     # if key_name not in self.keymap.keys():
        #     #     return
        #     _cmd_str = self.keymap.get(key_name)
        #     self.__log.debug("%s>_cmd_str=%s", key_name, _cmd_str)

        # self.__log.debug("_cmd_str=%a", _cmd_str)

        if _cmd_str:
            self.jrpc_clnt.jrpc_call(_cmd_str)

    def main(self):
        """Main."""
        self.__log.debug("")

        print("Start..")

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
                self.__log.debug("input_dev=%s", self.input_dev)
                if self.input_dev:
                    print("Ready")

            except IndexError as e:
                # BlueTooth is lost ?
                if not self.input_dev:
                    self.__log.error(
                        "device not found:%a", self.btdev_keyword
                    )
                    time.sleep(2)
                    self.input_dev = self.bt_input.search_input_devs(
                        self.btdev_keyword
                    )
                    self.__log.debug("input_dev=%s", self.input_dev)
                    if self.input_dev:
                        print("Ready")
                else:
                    self.__log.error(errmsg(e))

            except Exception as e:
                self.__log.error(errmsg(e))
                import traceback

                print(traceback.format_exc())

    def end(self):
        """End."""
        self.__log.debug("")
