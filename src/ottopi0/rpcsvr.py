#
# (c) 2025 Yoichi Tanibayashi
#
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from jsonrpc import JSONRPCResponseManager, dispatcher

from .func_calc import Calc
from .utils.mylogger import get_logger

ENV_DEBUG = "SVR_DEBUG"


@asynccontextmanager
async def lifespan(api: FastAPI):
    """Lifespan manager for the application."""
    debug = os.getenv(ENV_DEBUG) == "1"
    api.state.debug = debug

    __log = get_logger(__name__, debug)
    __log.debug("debug=%s", debug)

    # _calc = Calc()
    # dispatcher.add_method(_calc.add)
    # dispatcher.add_method(_calc.sub)
    # dispatcher.add_method(_calc.calc)
    dispatcher.add_class(Calc)

    __log.debug("dispatcher: %s", [func for func in dispatcher])

    yield


api = FastAPI(lifespan=lifespan)


@api.post("/api")
async def handle_req(request: Request):
    """API."""
    __debug = request.app.state.debug
    __log = get_logger(__name__, __debug)

    _req_body: bytes = await request.body()
    _req_str: str = _req_body.decode("utf-8")
    __log.debug("req_str=%s", _req_str)

    _res = JSONRPCResponseManager.handle(_req_str, dispatcher)

    if _res:
        __log.debug("res.data=%s", _res.data)
        __log.debug("res.json=%s: %s", _res.json, type(_res.json).__name__)
        return _res.data
    else:
        return {}
