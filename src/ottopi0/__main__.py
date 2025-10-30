#
# (c) 2025 Yoichi Tanibayashi
#
"""__main__.py"""

import click

from . import __version__
from .utils.clickutils import click_common_opts
from .utils.mylogger import get_logger


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
@click_common_opts(__version__)
def svr(ctx, debug):
    """Ir Analyze."""
    __log = get_logger(__name__, debug)
    __log.debug("cmd_name=%s", ctx.command.name)

    # app = None
    # try:
    #     app = Svr(debug=debug)
    #     app.main()

    # except Exception as _e:
    #     __log.error(errmsg(_e))

    # finally:
    #     if app:
    #         app.end()
