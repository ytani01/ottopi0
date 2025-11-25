#
# (c) 2025 Yoichi Tanibayashi
#
import os
from contextlib import asynccontextmanager

import pigpio
from fastapi import FastAPI, Request
from jsonrpc import JSONRPCResponseManager, dispatcher

from . import ENV_DEBUG
from .func_calc import Calc
from .func_servo import Servo
from .utils.mylogger import errmsg, get_logger


@asynccontextmanager
async def lifespan(api: FastAPI):
    """Lifespan manager for the application."""
    debug = os.getenv(ENV_DEBUG) == "1"

    __log = get_logger(__name__, debug)
    __log.debug("ENV_DEBUG=%a, value=%s", ENV_DEBUG, debug)

    # ``{api}.state.{変数名}`` の内容は、
    # ハンドラーでは、``reqeust.app.state.{変数名}`` で参照できる
    api.state.debug = debug
    __log.debug("api.state=%s", api.state.__dict__)

    # class単位で登録
    # "calc.method" という名前になる
    dispatcher.add_class(Calc)

    ### pigpio
    pi = pigpio.pi()

    ### servo
    pins_str = os.environ[f"{__package__}_PINS"]
    servo_pins = [int(p) for p in pins_str.split(",")]
    __log.debug("servo_pins=%s", servo_pins)

    angle_factors_str = os.environ[f"{__package__}_ANGLE_FACTORS"]
    angle_factors = [int(p) for p in angle_factors_str.split(",")]
    __log.debug("angle_factors=%s", angle_factors)

    servo = Servo(pi, servo_pins, angle_factors, debug=debug)
    servo._start()

    dispatcher.add_object(servo)

    ###
    __log.debug("dispatcher: %s", [func for func in dispatcher])

    yield

    servo._end()

    try:
        pi.stop()
    except Exception as _e:
        __log.error(errmsg(_e))


api = FastAPI(lifespan=lifespan)


@api.post("/api")
async def handle_req(request: Request):
    """API."""
    __debug = request.app.state.debug
    __log = get_logger(__name__, __debug)
    __log.debug("request.app.state=%s", request.app.state.__dict__)

    # ポストされたリクエスト(JSON)を取得
    _req_body: bytes = await request.body()
    _req_str: str = _req_body.decode("utf-8")
    __log.debug("req_str=%s", _req_str)

    _res = JSONRPCResponseManager.handle(_req_str, dispatcher)
    if _res:
        __log.debug("res.data=%s: %s", _res.data, type(_res.data).__name__)
        # __log.debug("res.json=%s: %s", _res.json, type(_res.json).__name__)
        if isinstance(_res.data, dict):
            __log.debug("result=%s", _res.data.get("result"))
        return _res.data  # returnは、dict型でよい
    else:
        return {}
