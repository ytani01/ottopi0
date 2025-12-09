#
# (c) 2025 Yoichi Tanibayashi
#
import requests

from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import errmsg, get_logger


class Client:
    """JSON-RPC Client."""

    TRANSACTION_SEPARATOR = ";"  # トランザクション(cancelできる単位)の区切り

    def __init__(self, url: str, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("url=%s", url)

        self.url = url

        # load config
        self.conf = ConfFile(debug=self.__debug).conf
        self.funcs = self.conf.servo.funcs
        self.cmd_prefix = self.funcs._prefix

        # objects
        self.cslib = CmdStrLib(debug=self.__debug)

        # instance variables
        self.rpc_id = 0

    def jrpc_call(self, cmd_str: str):
        """JSON-RPC call."""
        self.__log.debug("cmd_str=%s", cmd_str)

        if not cmd_str:
            return None

        cmd_str = self.cslib.expand_func(cmd_str)
        self.__log.debug("cmd_str=%a", cmd_str)

        cmd_str_list = cmd_str.split(self.TRANSACTION_SEPARATOR)

        result = None

        for cmd_str in cmd_str_list:
            cmd_str = cmd_str.strip()

            if not cmd_str:
                continue

            self.__log.info("cmd_str=%a", cmd_str)

            self.rpc_id += 1

            cmd_str = f"{self.cmd_prefix} {cmd_str}".strip()

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
                return None

            result = response.json()
            if "result" in result:
                self.__log.info("result: %s", result["result"])
            elif "error" in result:
                self.__log.info("error: %s", result["error"])

        if result:
            return result
        else:
            return None
