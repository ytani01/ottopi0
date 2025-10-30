#
# (c) 2025 Yoichi Tanibayashi
#
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from jsonrpc import JSONRPCResponseManager, dispatcher

from .utils.mylogger import get_logger

ENV_DEBUG = "SVR_DEBUG"


class Robot:
    """Robot class."""

    def __init__(self, debug=False) -> None:
        """Constractor."""

        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)

        self.__log.debug("Hello")

    def main(self):
        """Main."""
        self.__log.debug("")

    def end(self):
        """End."""
        self.__log.debug("")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the application."""
    debug = os.getenv(ENV_DEBUG) == "1"
    print(f"debug={debug}")

    __log = get_logger(__name__, debug)
    __log.debug("debug=%s", debug)

    app.state.svr_app = Robot(debug=debug)
    app.state.debug = debug

    yield

    app.state.svr_app.end()


app = FastAPI(lifespan=lifespan)


@dispatcher.add_method
def add(a: float, b: float) -> float:
    """Add function."""
    return a + b


@app.post("/api")
async def handle(request: Request):
    """API."""
    print(__name__)
    _req_body: bytes = await request.body()
    _req_str: str = _req_body.decode("utf-8")
    print(_req_str)

    _app = request.app.state.svr_app
    _app.main()

    _res = JSONRPCResponseManager.handle(_req_str, dispatcher)

    if _res:
        print(_res.data)
        return _res.data
    else:
        return {}
