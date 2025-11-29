#
# (c) 2025 Yoichi Tanibayashi
#
from pi0servo import JsonRpcWorker, StrCmdToJson

from .. import get_logger


class Servo:
    """Servo."""

    def __init__(self, pi, pins, angle_factors, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("pins=%s, angle_factors=%s", pins, angle_factors)

        self.pi = pi
        self.pins = pins
        self.angle_factors = angle_factors

        self.parser = StrCmdToJson(self.angle_factors, debug=self.__debug)
        self.servo = JsonRpcWorker(self.pi, self.pins, debug=self.__debug)

    def _start(self):
        """Start."""
        self.__log.debug("")
        self.servo.start()

    def _end(self):
        """End."""
        self.__log.debug("")
        self.servo.end()
        self.__log.debug("done")

    def call(self, cmd_str):
        """Call."""
        self.__log.debug("cmd_str=%s", cmd_str)

        jrpcstr = self.parser.cmdstr_to_jsonliststr(cmd_str)
        self.__log.debug("jrpcstr=%s", jrpcstr)

        ret = self.servo.call(jrpcstr)
        self.__log.debug("servo.call(%s)", jrpcstr)
        return ret
