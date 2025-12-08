#
# (c) 2025 Yoichi Tanibayashi
#
import time

import pigpio
from vl53l0x_pigpio import VL53L0X

from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import get_logger
from .jrpcclnt import JrpcClient


class JrpcClntDistance:
    """JSON-RPC Client: distance sensor."""

    def __init__(self, url: str, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("url=%s", url)

        self.url = url

        # config file
        self.conf = ConfFile().conf
        self.auto = self.conf.auto
        self.funcs = self.conf.servo.funcs

        self.distance_near = self.auto.distance.get("near")
        self.distance_far = self.auto.distance.get("far")
        self.__log.debug(
            "distance_near=%s, distance_far=%s",
            self.distance_near,
            self.distance_far,
        )

        self.cmd_auto_stop = self.funcs.get("auto-stop")
        self.__log.debug("cmd_auto_stop=%a", self.cmd_auto_stop)

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

        count = 0
        while self.is_active:
            count += 1
            if count > 10:
                self.jrpc_clnt.jrpc_call("ms:.2 f:forward")
                count = 0

            try:
                distance = self.tof.get_range()
                self.__log.debug("distance=%s", distance)
            except EOFError:
                print("\nEOF")
                break

            if distance < self.distance_near:
                self.jrpc_clnt.jrpc_call(self.cmd_auto_stop)
                self.jrpc_clnt.jrpc_call("ww")
                time.sleep(0.01)

            time.sleep(0.05)

    def end(self):
        """End."""
        self.__log.debug("")
        self.tof.close()
        self.pi.stop()
