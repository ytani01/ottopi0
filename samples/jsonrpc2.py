import click
import json

from jsonrpc import JSONRPCResponseManager, Dispatcher
from ottopi0 import get_logger, click_common_opts, errmsg


class Func:
    """Func."""
    def __init__(self, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

    def func1(self, a):
        return f"func1 {a}"

    def func2(self, a, b):
        return f"func2 {a} {b}"


class App:
    """App."""

    def __init__(self, debug=False) -> None:
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.rpc_id = 1

        self.dispacher = Dispatcher()
        self.dispacher.add_class(Func)

    def main(self):
        """Main."""
        self.__log.debug("")

        while True:
            try:
                line  = input("> ")
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
