#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import version as get_version

from dynaconf import Dynaconf

from .utils.clibase import CliBase, CliWithHistory, OneKeyCli, ScriptRunner
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

__version__ = "_._._"
if __package__:
    __version__ = get_version(__package__)

Config = Dynaconf(settings_files=["ottopi0.toml"])

ENV_DEBUG = f"{__package__}_DEBUG"

__all__ = [
    "__version__",
    "ENV_DEBUG",
    "click_common_opts",
    "Config",
    "errmsg",
    "get_logger",
    "CliBase",
    "CliWithHistory",
    "ScriptRunner",
    "OneKeyCli",
]
