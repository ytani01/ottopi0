#
# (c) 2025 Yoichi Tanibayashi
#
import os
from importlib.metadata import version as get_version

from dynaconf import Dynaconf

from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

# Version string
__version__ = "_._._"
if __package__:
    __version__ = get_version(__package__)
    PKGNAME = __package__

# Config
SETTINGS_FILE1 = "ottopi0.toml"
SETTINGS_FILE2 = os.path.expanduser("~/ottopi0.toml")
# 後ろのほうが設定を上書きする
Config = Dynaconf(settings_files=[SETTINGS_FILE1, SETTINGS_FILE2])

# env variables
ENVNAME_DEBUG = f"{__package__}_DEBUG"

#
__all__ = [
    "__version__",
    "ENVNAME_DEBUG",
    "PKGNAME",
    "click_common_opts",
    "Config",
    "errmsg",
    "get_logger",
]
