#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import os

import click
import uvicorn

from . import __version__
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger


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
    "--host",
    "-i",
    type=str,
    default="0.0.0.0",
    show_default=True,
    help="hostname or ipaddr",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=8000,
    show_default=True,
    help="port number",
)
@click_common_opts(__version__)
def svr(ctx, host, port, debug):
    """Ir Analyze."""
    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)
    __log.debug("host=%s, port=%s", host, port)

    APP = "ottopi0.svr:app"
    ENV_DEBUG = "SVR_DEBUG"

    os.environ[ENV_DEBUG] = "1" if debug else "0"

    try:
        uvicorn.run(
            APP,
            host=host,
            port=port,
            reload=True,
            log_level="debug" if debug else "warning",
        )

    except Exception as _e:
        __log.error(errmsg(_e))

    finally:
        click.echo("END.")
