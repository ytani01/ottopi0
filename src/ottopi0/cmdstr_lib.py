#
# (c) 2025 Yoichi Tanibayashi
#
from .conf_file import ConfFile
from .utils.mylogger import get_logger


class CmdStrLib:
    """Command string."""

    PREFIX_FUNC = "f:"
    EXPAND_FUNC_DEPTH_MAX = 10

    def __init__(self, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.conf = ConfFile(debug=self.__debug).conf
        self.funcs = self.conf.servo.funcs
        # self.__log.debug("funcs=%s", self.funcs)

    def expand_func(self, cmdline, depth=0, depth_max=EXPAND_FUNC_DEPTH_MAX):
        """Expand command function.

        "f:func_name" をコマンド列に展開する。

        e.g.
        f:xxx = "mv:11,11 mv:22,22"
        "mv:10,20 f:xxx mv:30,40"
        --> "mv:10,20  mv:11,11 mv:22,22  mv:30:40"
        """
        self.__log.debug(
            "cmdline=%a,depth=%s,depth_max=%s", cmdline, depth, depth_max
        )

        if depth > depth_max:
            self.__log.warning(
                "depth(%s) > depth_max(%s): stop recursive call.",
                depth,
                depth_max,
            )
            return ""

        cmd_list = []
        for cmd in cmdline.split():
            if not cmd:
                continue

            print(f"cmd={cmd}")
            if not cmd.startswith(self.PREFIX_FUNC):
                #
                # normal command string
                #
                cmd_list.append(cmd)
                continue

            #
            # expand function
            #
            funcname = cmd.split(":")[1]
            # self.__log.debug("funcname=%a", funcname)

            cmd2 = self.funcs.get(funcname)
            if cmd2:
                self.__log.debug("%a -> %a", funcname, cmd2)
                cmd2 = self.expand_func(cmd2, depth + 1)  # TBD recursive
                if cmd2:
                    cmd_list += cmd2.split()

        self.__log.debug("cmd_list=%s", cmd_list)

        cmdline = " ".join(cmd_list)
        return cmdline
