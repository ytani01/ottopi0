import json

import click
from jsonrpc import Dispatcher, JSONRPCResponseManager

from ottopi0 import CliWithHistory, click_common_opts, get_logger


class Func:
    """Func."""

    def __init__(self, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

    def func1(self):
        return "func1"

    def func2(self):
        return "func2"


class Cli(CliWithHistory):
    """CLI."""

    HISTORY_FILE = "/tmp/hist"

    def __init__(self, debug=False):
        super().__init__(history_file=self.HISTORY_FILE, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.id = 1

        self.dispacher = Dispatcher()
        self.dispacher.add_class(Func)

    def parse_instr(self, instr: str) -> dict:
        self.__log.debug("instr=%s", instr)
        args = instr.split()
        self.__log.debug("args=%s", args)

        parsed_data = {
            "data": {
                "method": args[0],
                "params": args[1:],
                "jsonrpc": "2.0",
                "id": self.id,
            },
            "status": Cli.RESULT_STATUS["OK"],
        }
        self.__log.debug("parsed_data=%s", parsed_data)

        self.id += 1
        return parsed_data

    def handle(self, parsed_data: dict) -> dict:
        self.__log.debug("parsed_data=%s", parsed_data)

        data_json = json.dumps(parsed_data["data"])
        self.__log.debug("data_json=%s", data_json)

        ret = JSONRPCResponseManager.handle(data_json, self.dispacher)
        self.__log.debug("ret=%s", ret)

        if ret:
            result_data = {
                "status": Cli.RESULT_STATUS["OK"],
                "data": ret.data,
            }
        else:
            result_data = {
                "status": Cli.RESULT_STATUS["ERR"],
            }
        return result_data


@click.command()
@click_common_opts("0.0.1")
def main(ctx, debug):
    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)

    app = None
    try:
        app = Cli(debug=debug)
        app.main()
    finally:
        if app:
            app.end()


if __name__ == "__main__":
    main()
