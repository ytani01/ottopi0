#
# (c) 2025 Yoichi Tanibayashi
#
import os

from dynaconf import Dynaconf

from .utils.mylogger import get_logger


class ConfFile:
    """Config file."""

    SETTINGS_FILES = [
        "ottopi0.toml",
        "~/ottopi0.toml",
    ]

    def __init__(self, debug=False):
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.settings_files = []
        for f in self.SETTINGS_FILES:
            self.settings_files.append(
                os.path.expanduser(os.path.expandvars(f))
            )

        self._config = Dynaconf(settings_files=self.settings_files)

    @property
    def conf(self):
        return self._config
