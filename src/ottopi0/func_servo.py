#
# (c) 2025 Yoichi Tanibayashi
#
import os
import pigpio
import pi0servo

from . import ENV_DEBUG, get_logger

class Servo:
    """Servo."""

    def __init__(self) -> None:
        self.__debug = os.environ[ENV_DEBUG] == "1"
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        pins_str = os.environ[f"{__package__}_PINS"]
        self.pins = [int(p) for p in pins_str.split(",")]
        self.__log.debug("pins=%s", self.pins)

        angle_factors_str = os.environ[f"{__package__}_ANGLE_FACTORS"]
        self.angle_factors = [int(p) for p in angle_factors_str.split(",")]
        self.__log.debug("angle_factors=%s", self.angle_factors)

        self.pi = pigpio.pi()

        self.parser = pi0servo.StrCmdToJson(
            self.angle_factors, debug=self.__debug
        )
        self.servo = pi0servo.JsonRpcWorker(
            self.pi, self.pins, debug=self.__debug
        )

    def _start(self):
        """Start."""
        self.__log.debug("")
        self.servo.start()

    def _end(self):
        self.__log.debug("")
        self.servo.end()
        self.pi.stop()

    def foo(self):
        self.__log.debug("")
        return "foo"

    def call(self, cmd_str):
        """Call."""
        self.__log.debug("cmd_str=%s", cmd_str)

        jsonrpcstr = self.parser.cmdstr_to_jsonliststr(cmd_str)
        self.__log.debug("jsonrpcstr=%s", jsonrpcstr)

        ret = self.servo.call(jsonrpcstr)
        return ret
