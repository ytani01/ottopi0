#
# (c) 2025 Yoichi Tanibayashi
#
import os
import readline

import requests

from ..cmdstr_lib import CmdStrLib
from ..conf_file import ConfFile
from ..utils.mylogger import errmsg, get_logger


class RpcClntCli:
    """RPC Client: CLI."""

    def __init__(self, history_file: str, url: str, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("url=%s, history_file=%a", url, history_file)

        self.history_file = history_file
        self.url = url

        # load config
        self.conf = ConfFile(debug=self.__debug).conf
        self.funcs = self.conf.servo.funcs
        self.cmd_prefix = self.funcs._prefix
        # self.__log.debug("funcs=%s, self.funcs)
        self.__log.debug("cmd_prefix=%a", self.cmd_prefix)

        self.cslib = CmdStrLib(self.__debug)

        # history file
        self.history_file = os.path.expanduser(
            os.path.expandvars(history_file)
        )
        self.__log.debug("history_file=%a", self.history_file)

        try:
            readline.read_history_file(self.history_file)
            self.__log.debug("hist_len=%s", readline.get_history_length)
        except FileNotFoundError:
            self.__log.warning("no history file: %s", self.history_file)
        except OSError:
            self.__log.warning(
                "invalid history file .. remove: %s", self.history_file
            )
            os.remove(self.history_file)
        except Exception as e:
            self.__log.error(errmsg(e))

        # instance variables
        self.prompt = f"{__package__}> "
        self.__log.debug("prompt=%a", self.prompt)

        self.is_active = True
        self.rpc_id = 0

    def main(self):
        """Main."""
        self.__log.debug("")

        print("[Ctrl]-D for exit")

        while self.is_active:
            try:
                instr = input(self.prompt)
                self.__log.debug("instr=%a", instr)
            except EOFError:
                print("\nEOF")
                break

            # remove comment string
            instr = instr.partition("#")[0]
            self.__log.debug("remove comment: instr=%a", instr)

            # expand function (recursive)
            cmdline = self.cslib.expand_func(f"{self.cmd_prefix} {instr}")
            self.__log.debug("cmdline=%a", cmdline)

            if cmdline != self.cmd_prefix:
                self.rpc_call(cmdline)

    def end(self):
        """End."""
        self.__log.debug("")

        # history file
        try:
            readline.write_history_file(self.history_file)
        except Exception as e:
            self.__log.error("%s: %s", self.history_file, errmsg(e))

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

        result = response.json()
        if "result" in result:
            self.__log.debug("result: %s", result["result"])
        elif "error" in result:
            self.__log.debug("error: %s", result["error"])
