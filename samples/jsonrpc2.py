import json

import click
from jsonrpc import Dispatcher, JSONRPCResponseManager

from ottopi0 import click_common_opts, errmsg, get_logger


class Func:
    """Func."""

    def __init__(self, hdr, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.hdr = hdr

    def func1(self, a):
        self.__log.debug("a=%s", a)
        return f"{self.hdr}: func1 {a}"

    def func2(self, a, b):
        self.__log.debug("a=%s,b=%s", a, b)
        return f"{self.hdr}: func2 {a} {b}"


class App:
    """App."""

    def __init__(self, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.rpc_id = 1

        self.dispacher = Dispatcher()
        self.obj_func = Func("AAA", debug=self.__debug)
        self.dispacher.add_object(self.obj_func)

    def main(self):
        """Main."""
        self.__log.debug("")

        while True:
            try:
                line = input("> ")
                if not line:
                    continue
            except EOFError:
                break

            args = line.split()

            rpc_req_data = {
                "method": args[0],
                "params": args[1:],
                "jsonrpc": "2.0",
                "id": self.rpc_id,
            }

            rpc_req_jsonstr = json.dumps(rpc_req_data)
            self.__log.debug("rpc_req_jsonstr=%a", rpc_req_jsonstr)

            ret = None
            try:
                ret = JSONRPCResponseManager.handle(
                    rpc_req_jsonstr, self.dispacher
                )
            except Exception as e:
                self.__log.error(errmsg(e))

            if ret:
                print(f"ret={ret.data}")


@click.command()
@click_common_opts("0.0.1")
def main(ctx, debug):
    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)

    app = None
    try:
        app = App(debug=debug)
        app.main()
    finally:
        print("finally")


if __name__ == "__main__":
    main()
