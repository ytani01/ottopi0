#
# (c) 2025 Yoichi Tanibayashi
#
import json

from pi0servo import JsonRpcWorker, StrCmdToJson

from .. import get_logger


class Servo:
    """Servo."""

    def __init__(self, pi, pins, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("pins=%s", pins)

        self.pi = pi
        self.pins = pins

        self.parser = StrCmdToJson(debug=self.__debug)
        self.servo = JsonRpcWorker(
            self.pi, self.pins, flag_verbose=True, debug=False
        )

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

        jrpcreq = self.parser.cmdstr_to_jsonlist(cmd_str)
        self.__log.debug("jrpcreq=%s", jrpcreq)

        ret = self.servo.call(jrpcreq)
        self.__log.info("ret = %s", json.dumps(ret, indent=2))
        return ret
