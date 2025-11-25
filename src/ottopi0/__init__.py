#
# (c) 2025 Yoichi Tanibayashi
#
import os
from importlib.metadata import version as get_version

from dynaconf import Dynaconf

from .utils.clibase import CliBase, CliWithHistory, OneKeyCli, ScriptRunner
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

__version__ = "_._._"
if __package__:
    __version__ = get_version(__package__)

SETTINGS_FILE1 = "ottopi0.toml"
SETTINGS_FILE2 = os.path.expanduser("~/ottopi0.toml")
# 後ろのほうが設定を上書きする
Config = Dynaconf(settings_files=[SETTINGS_FILE1, SETTINGS_FILE2])

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
