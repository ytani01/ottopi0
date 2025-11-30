#
# (c) 2025 Yoichi Tanibayashi
#
import time

import pigpio
from vl53l0x_pigpio import VL53L0X

from ..cmdstr_lib import CmdStrLib
from ..jrpcclnt import JrpcClient
from ..utils.mylogger import get_logger


class JrpcClntDistance:
    """JSON-RPC Client: distance sensor."""

    CMD_STOP = "f:home f:turn-r"

    def __init__(self, url: str, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("url=%s", url)

        self.url = url

        # common objects
        self.pi = pigpio.pi()
        self.tof = VL53L0X(self.pi)
        self.cslib = CmdStrLib(self.__debug)
        self.jrpc_clnt = JrpcClient(self.url, debug=self.__debug)

        # instance variables
        self.is_active = True
        self.mode = ""
        self.jrpc_id = 0

    def main(self):
        """Main."""
        self.__log.debug("")

        while self.is_active:
            try:
                distance = self.tof.get_range()
                self.__log.debug("distance=%s", distance)
            except EOFError:
                print("\nEOF")
                break

            if distance < 300:
                self.jrpc_clnt.jrpc_call(self.CMD_STOP)
                time.sleep(10)

    def end(self):
        """End."""
        self.__log.debug("")
        self.tof.close()
        self.pi.stop()
