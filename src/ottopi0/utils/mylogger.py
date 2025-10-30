#
# (c) 2025 Yoichi Tanibayashi
#
"""
Usage:

  class AAA:
      def __init__(self, debug_flag):
          #
          #   継承時にoverrideされないように、'__'をつける
          #
          self.__log = get_logger(__class__.__name__, debug=debug_flag)
          self.__log.debug("....")

  def main(debug_flag):
      log = get_logger(__name__, debug=debug_flag)
      log.debug("....")

"""

import inspect
from logging import DEBUG, INFO, Formatter, StreamHandler, getLogger


def get_logger(name, debug=False):
    """Get logger."""
    filename = inspect.stack()[1].filename.split("/")[-1]
    name = filename + "." + name
    logger = getLogger(name)

    # Prevent messages from being passed to the root logger
    logger.propagate = False

    # Clear existing handlers to prevent duplicates
    # if get_logger is called multiple times for the same name
    if logger.handlers:
        logger.handlers.clear()

    # Create a new handler and formatter for each logger
    fmt_hdr = "%(asctime)s %(levelname)s "
    fmt_loc = "%(name)s.%(funcName)s:%(lineno)d> "
    handler_fmt = Formatter(
        fmt_hdr + fmt_loc + "%(message)s", datefmt="%H:%M:%S"
    )

    console_handler = StreamHandler()
    console_handler.setFormatter(handler_fmt)
    console_handler.setLevel(DEBUG)

    logger.addHandler(console_handler)
    logger.setLevel(INFO)  # Default logger level

    # [Important !! ]
    # isinstance()では、boolもintと判定されるので、
    # 先に bool かどうかを判定する

    if isinstance(debug, bool):
        if debug:
            logger.setLevel(DEBUG)
        return logger

    if isinstance(debug, int):
        logger.setLevel(debug)
        return logger

    raise ValueError("invalid `debug` value: %s" % (debug))


def errmsg(e) -> str:
    """Make stantdard error message."""
    e_name = type(e).__name__
    if type(e).__module__ != "builtins":
        e_name = f"{type(e).__module__}.{e_name}"
    return f"{e_name}: {e}"
