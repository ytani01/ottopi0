#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import os

import click
import uvicorn

from . import ENV_DEBUG, Config,  __version__
from .rpcclnt_bt import RpcClntBt
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger


DEF_SERVO_PINS = list(Config.servo.pins)
click.echo(f"DEF_SERVO_PINS={DEF_SERVO_PINS}")
DEF_SERVO_ANGLE_FACTORS = list(Config.servo.angle_factors)
click.echo(f"DEF_SERVO_ANGLE_FACTORS={DEF_SERVO_ANGLE_FACTORS}")

DEF_PROTO = Config.rpc.proto
DEF_HOST = Config.rpc.host
DEF_PORT = Config.rpc.port
DEF_APIPATH = Config.rpc.apipath
DEF_URL = f"{DEF_PROTO}://{DEF_HOST}:{DEF_PORT}{DEF_APIPATH}"
click.echo(f"DEF_URL={DEF_URL}")


@click.group()
@click_common_opts(__version__)
def cli(ctx, debug):
    """pi0servo CLI top."""
    cmd_name = ctx.info_name
    subcmd_name = ctx.invoked_subcommand

    ___log = get_logger(cmd_name, debug)

    ___log.debug("cmd_name=%s, subcmd_name=%s", cmd_name, subcmd_name)

    if subcmd_name is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("pins", type=str, nargs=1)
@click.argument("angle_factors", type=str, nargs=1)
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_PORT,
    show_default=True,
    help="port number",
)
@click_common_opts(__version__)
def rpcsvr(ctx, pins, angle_factors, host, port, debug):
    """JSON-RPC 2.0 server.

    e.g.

    PINS: 16,19.26,20

    AGNLE_FACTORS: mpmp (= -1,1,-1,1)
    

    # sample client

    ```sh

    curl -X POST -H "Content-Type: application/json" \\

    -d '{

    "jsonrpc": "2.0", "id":1, \\

    "method": "servo.call", "params": ["mv:30,-30,-30,30"] \\

    }' \\
    
    http://localhost:8000/api

    ```
    """
    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)
    __log.debug("pins=%s, angle_factors=%s", pins, angle_factors)
    __log.debug("host=%s, port=%s", host, port)

    if len(pins.split(",")) != len(angle_factors):
        __log.error(
            "invalid length of angle_factor:%a, len=%d",
            angle_factors,
            len(angle_factors),
        )
        return

    # e.g. "mpmp" -> "-1,1,-1,1"
    af_list = []
    for ch in angle_factors:
        if ch == "p":
            af_list.append(1)
        elif ch == "m":
            af_list.append(-1)
        else:
            __log.error("invalid angle factor charactor: %s", ch)
            return

    af_list_str = ",".join(map(str, af_list))
    __log.debug("af_list_str=%s", af_list_str)

    click.echo(f"ENV_DEBUG={ENV_DEBUG}")
    os.environ[ENV_DEBUG] = "1" if debug else "0"

    os.environ[f"{__package__}_PINS"] = f"{pins}"
    os.environ[f"{__package__}_ANGLE_FACTORS"] = f"{af_list_str}"

    # start API
    _api = f"{__package__}.rpcsvr:api"
    click.echo(f"_api={_api}")

    try:
        uvicorn.run(
            _api,
            host=host,
            port=port,
            reload=True,
            log_level="debug" if debug else "info",
        )

    except Exception as _e:
        __log.error(errmsg(_e))

    finally:
        click.echo("END.")


@cli.command()
@click.argument("btdev_keyword", type=str, nargs=-1)
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_PORT,
    show_default=True,
    help="port number",
)
@click_common_opts(__version__)
def rpcclntbt(ctx, btdev_keyword, host, port, debug):
    """JSON-RPC Client for BlueTooth controller."""
    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "btdev_keyword=%s, host=%s, port=%s", btdev_keyword, host, port
    )

    if len(btdev_keyword) == 0:
        __log.error("no btdev_keyword:%s", btdev_keyword)
        return

    url = f"http://{host}:{port}/api"
    __log.debug("url=%s", url)

    app = None
    try:
        app = RpcClntBt(btdev_keyword, url, debug=debug)
        app.main()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        if app:
            app.end()
        click.echo("Done.")
