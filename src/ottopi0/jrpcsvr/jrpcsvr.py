#
# (c) 2025 Yoichi Tanibayashi
#
import json
import os
from contextlib import asynccontextmanager

import pigpio
from fastapi import FastAPI, Request
from jsonrpc import JSONRPCResponseManager, dispatcher
from pi0servo import CommonLib

from .. import ENVNAME_DEBUG, PKGNAME, errmsg, get_logger
from .func_calc import Calc
from .func_servo import Servo


@asynccontextmanager
async def lifespan(api: FastAPI):
    """Lifespan manager for the application."""
    __debug = os.getenv(ENVNAME_DEBUG) == "1"

    __log = get_logger(__name__, __debug)
    __log.debug("ENVNAME_DEBUG=%a, value=%s", ENVNAME_DEBUG, __debug)

    # ``{api}.state.{変数名}`` の内容は、
    # ハンドラーでは、``reqeust.app.state.{変数名}`` で参照できる
    api.state.debug = __debug
    __log.debug("api.state=%s", api.state.__dict__)

    # class単位で登録
    # "calc.method" という名前になる
    dispatcher.add_class(Calc)

    # sv_common = CommonLib(debug=__debug)
    sv_common = CommonLib()

    ### pigpio
    pi = pigpio.pi()

    ### servo
    __log.debug("PKGNAME=%s", PKGNAME)
    pins_str = os.environ[f"{PKGNAME}_SERVO_PINS"]

    servo_pins = sv_common.pins_str2list(pins_str)
    __log.debug("servo_pins=%s", servo_pins)

    servo = Servo(pi, servo_pins, debug=__debug)
    servo._start()

    dispatcher.add_object(servo)
    __log.debug("dispatcher: %s", [func for func in dispatcher])

    __log.info("Ready")

    yield

    __log.info("Shutdown..")

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
    # __log.info("req_str=%s", _req_str)

    _req_json = json.loads(_req_str)
    __log.info("%s%s", _req_json.get("method"), _req_json.get("params"))

    _res = JSONRPCResponseManager.handle(_req_str, dispatcher)
    if _res:
        __log.info("res.data=%s: %s", _res.data, type(_res.data).__name__)
        # __log.debug("res.json=%s: %s", _res.json, type(_res.json).__name__)
        if isinstance(_res.data, dict):
            __log.debug("result=%s", _res.data.get("result"))
        return _res.data  # returnは、dict型でよい
    else:
        return {}
