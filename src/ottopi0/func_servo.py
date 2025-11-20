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

        self.servo = pi0servo.JsonRpcWorker(
            self.pi, self.pins, debug=self.__debug
        )


    def foo(self):
        pass
