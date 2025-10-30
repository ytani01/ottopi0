#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import version as get_version

__version__ = "_._._"
if __package__:
    __version__ = get_version(__package__)

from .utils.clibase import CliBase, CliWithHistory, OneKeyCli, ScriptRunner
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

__all__ = [
    "__version__",
    "click_common_opts",
    "errmsg",
    "get_logger",
    "CliBase",
    "CliWithHistory",
    "ScriptRunner",
    "OneKeyCli",
]
