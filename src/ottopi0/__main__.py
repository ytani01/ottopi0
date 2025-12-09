#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import click

from . import (
    ENVNAME_DEBUG,
    PKGNAME,
    ConfFile,
    __version__,
    click_common_opts,
    errmsg,
    get_logger,
)

# config file
Conf = ConfFile().conf

DEF_SERVO_PINS = Conf.servo.pins
DEF_HISTORY_FILE = Conf.jrpc.client.cli.history_file
DEF_BTDEV_KEYWORD = Conf.jrpc.client.bluetooth.dev_keyword
DEF_JRPC_PROTO = Conf.jrpc.server.proto
DEF_JRPC_HOST = Conf.jrpc.server.host
DEF_JRPC_PORT = Conf.jrpc.server.port
DEF_JRPC_APIPATH = Conf.jrpc.server.apipath

DEF_WEBUI_PORT = Conf.jrpc.client.webui.port
DEF_WEBUI_JRPC_HOST = Conf.jrpc.client.webui.jrpcsvr.host or DEF_JRPC_HOST
DEF_WEBUI_JRPC_PORT = Conf.jrpc.client.webui.jrpcsvr.port or DEF_JRPC_PORT
DEF_WEBUI_JRPC_APIPATH = (
    Conf.jrpc.client.webui.jrpcsvr.apipath or DEF_JRPC_APIPATH
)


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
    default=DEF_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_JRPC_PORT,
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
def svr(ctx, servo_pins, host, port, reload, debug):
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
    os.environ[f"{PKGNAME}_SERVO_PINS"] = f"{servo_pins}"

    # start API
    _api = f"{PKGNAME}.svr.svr:api"

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
@click.option(
    "--historyfile",
    "--hist",
    type=str,
    default=DEF_HISTORY_FILE,
    show_default=True,
    help="history file",
)
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_JRPC_PORT,
    show_default=True,
    help="port number",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_JRPC_APIPATH,
    show_default=True,
    help="API path",
)
@click_common_opts(__version__)
def cmd(ctx, historyfile, host, port, apipath, debug):
    """JSON-RPC Client for command line interface."""
    from .clnt.cmd import Cmd

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "historyfile=%a, host=%a,port=%s,apipath=%a",
        historyfile,
        host,
        port,
        apipath,
    )

    url = f"http://{host}:{port}{apipath}"
    __log.debug("url=%s", url)

    app = None
    try:
        app = Cmd(historyfile, url, debug=debug)
        app.main()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        if app:
            app.end()
        click.echo("Done.")


@cli.command()
@click.argument("btdev_keyword", type=str, nargs=-1)
@click.option(
    "--btdev",
    "-b",
    type=str,
    default=DEF_BTDEV_KEYWORD,
    show_default=True,
    help="BlueTooth device keyword",
)
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_JRPC_PORT,
    show_default=True,
    help="port number",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_JRPC_APIPATH,
    show_default=True,
    help="API path",
)
@click_common_opts(__version__)
def bt(ctx, btdev, btdev_keyword, host, port, apipath, debug):
    """JSON-RPC Client for BlueTooth controller."""
    from .clnt.bt import Bt

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "btdev=%s,host=%a,port=%s,apipath=%a",
        btdev,
        host,
        port,
        apipath,
    )

    if not btdev:
        __log.error("no btdev:%s", btdev_keyword)
        return
    btdev_keyword = btdev.split(",")

    url = f"http://{host}:{port}{apipath}"
    __log.debug("url=%s", url)

    app = None
    try:
        app = Bt(btdev_keyword, url, debug=debug)
        app.main()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        if app:
            app.end()
        click.echo("Done.")


@cli.command()
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_JRPC_PORT,
    show_default=True,
    help="port number",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_JRPC_APIPATH,
    show_default=True,
    help="API path",
)
@click_common_opts(__version__)
def auto(ctx, host, port, apipath, debug):
    """JSON-RPC Client for VL53L0X distance sensor."""
    from .clnt.auto import Auto

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "host=%a,port=%s,apipath=%a",
        host,
        port,
        apipath,
    )

    url = f"http://{host}:{port}{apipath}"
    __log.debug("url=%s", url)

    app = None
    try:
        app = Auto(url, debug=debug)
        app.main()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        if app:
            app.end()
        click.echo("Done.")


@cli.command(name="webui")
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_WEBUI_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr (of jrpcsvr)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_WEBUI_JRPC_PORT,
    show_default=True,
    help="port number (of jrpcsvr)",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_WEBUI_JRPC_APIPATH,
    show_default=True,
    help="API path (of jrpcsvr)",
)
@click.option(
    "--webui-port",
    "-w",
    type=int,
    default=DEF_WEBUI_PORT,
    show_default=True,
    help="port number for WebUI",
)
@click_common_opts(__version__)
def webui(ctx, host, port, apipath, webui_port, debug):
    """WebUI Client for Robot Control."""
    from .clnt.webui import WebUI

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "host=%a, port=%s, apipath=%a, webui_port=%s",
        host,
        port,
        apipath,
        webui_port,
    )

    url = f"http://{host}:{port}{apipath}"
    __log.debug("url=%s", url)

    app = None
    try:
        app = WebUI(url, webui_port=webui_port, debug=debug)
        app.run()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        click.echo("Done.")


@cli.command(name="nicegui")
@click.option(
    "--host",
    "-i",
    type=str,
    default=DEF_WEBUI_JRPC_HOST,
    show_default=True,
    help="hostname or ipaddr (of jrpcsvr)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=DEF_WEBUI_JRPC_PORT,
    show_default=True,
    help="port number (of jrpcsvr)",
)
@click.option(
    "--apipath",
    "-a",
    type=str,
    default=DEF_WEBUI_JRPC_APIPATH,
    show_default=True,
    help="API path (of jrpcsvr)",
)
@click.option(
    "--webui-port",
    "-w",
    type=int,
    default=DEF_WEBUI_PORT,
    show_default=True,
    help="port number for WebUI",
)
@click_common_opts(__version__)
def nicegui(ctx, host, port, apipath, webui_port, debug):
    """WebUI Client (NiceGUI) for Robot Control."""
    from .clnt.nicegui import NiceGUI

    __log = get_logger(__name__, debug)
    __log.debug("command name: %s", ctx.command.name)
    __log.debug(
        "host=%a, port=%s, apipath=%a, webui_port=%s",
        host,
        port,
        apipath,
        webui_port,
    )

    url = f"http://{host}:{port}{apipath}"
    __log.debug("url=%s", url)

    app = None
    try:
        app = NiceGUI(url, webui_port=webui_port, debug=debug)
        app.run()
    except Exception as _e:
        __log.error(errmsg(_e))
    finally:
        click.echo("Done.")
