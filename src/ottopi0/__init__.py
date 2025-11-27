#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import version as get_version

from .cmdstr_lib import CmdStrLib
from .conf_file import ConfFile
from .utils.clickutils import click_common_opts
from .utils.mylogger import errmsg, get_logger

# Version string
__version__ = "_._._"
if __package__:
    __version__ = get_version(__package__)
    PKGNAME = __package__

# env variables
ENVNAME_DEBUG = f"{__package__}_DEBUG"

#
__all__ = [
    "__version__",
    "ENVNAME_DEBUG",
    "PKGNAME",
    "click_common_opts",
    "ConfFile",
    "errmsg",
    "get_logger",
    "CmdStrLib",
]
