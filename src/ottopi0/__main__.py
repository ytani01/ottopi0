#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import click

from . import ENVNAME_DEBUG, Config, __version__
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

DEF_SERVO_PINS = Config.servo.pins

DEF_RPC_PROTO = Config.rpc.proto
DEF_RPC_HOST = Config.rpc.host
DEF_RPC_PORT = Config.rpc.port
DEF_RPC_APIPATH = Config.rpc.apipath


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
@click.option(
    "--servo-pins",
    "--pins",
    "-s",
    type=str,
    default=DEF_SERVO_PINS,
    show_default=True,
    help="servo pins",
)
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_RPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_RPC_PORT,
    show_default=True,
    help="port number",
)
@click.option(
    "--reload",
    "-r",
    is_flag=True,
    default=False,
    show_default=True,
    help="reload flag",
)
@click_common_opts(__version__)
def rpcsvr(ctx, servo_pins, host, port, reload, debug):
    """JSON-RPC 2.0 server.

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
    import os

    import uvicorn

    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)
    __log.debug("servo_pins=%a", servo_pins)
    __log.debug("host=%s, port=%s, reload=%s", host, port, reload)

    os.environ[ENVNAME_DEBUG] = "1" if debug else "0"
    os.environ[f"{__package__}_SERVO_PINS"] = f"{servo_pins}"

    # start API
    _api = f"{__package__}.rpcsvr:api"

    try:
        uvicorn.run(
            _api,
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if debug else "warning",
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
    default=DEF_RPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_RPC_PORT,
    show_default=True,
    help="port number",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_RPC_APIPATH,
    show_default=True,
    help="API path",
)
@click_common_opts(__version__)
def rpcclntbt(ctx, btdev_keyword, host, port, apipath, debug):
    """JSON-RPC Client for BlueTooth controller."""
    from .rpcclnt_bt import RpcClntBt

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "btdev_keyword=%s,host=%a,port=%s,apipath=%a",
        btdev_keyword,
        host,
        port,
        apipath,
    )

    if len(btdev_keyword) == 0:
        __log.error("no btdev_keyword:%s", btdev_keyword)
        return

    url = f"http://{host}:{port}{apipath}"
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
