#
# (c) 2025 Yoichi Tanibayashi
#
import os
import readline

from ..jrpcclnt import JrpcClient
from ..utils.mylogger import errmsg, get_logger


class JrpcClntCli:
    """JSON-RPC Client: CLI."""

    def __init__(self, history_file: str, url: str, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("url=%s, history_file=%a", url, history_file)

        self.history_file = history_file
        self.url = url

        # objects
        self.jrpcclnt = JrpcClient(self.url, debug=self.__debug)

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
        self.jrpc_id = 0

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

            result = self.jrpcclnt.jrpc_call(instr)
            self.__log.debug("result=%s", result)

    def end(self):
        """End."""
        self.__log.debug("")

        # history file
        try:
            readline.write_history_file(self.history_file)
        except Exception as e:
            self.__log.error("%s: %s", self.history_file, errmsg(e))
