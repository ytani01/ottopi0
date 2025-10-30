#
# (c) 2025 Yoichi Tanibayashi
#
"""CLI base"""

import os
import readline

import blessed

from .mylogger import errmsg, get_logger


class CliBase:
    """CLI base class"""

    PROMPT_STR = "> "

    RESULT_STATUS = {
        "OK": 0,
        "END": -1,
        "ERR": 1,
    }

    CMD_EXIT = [
        "exit",
        "quit",
    ]

    def __init__(self, prompt_str: str = PROMPT_STR, debug=False):
        """Contractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("prompt_str=%a", prompt_str)

        self.prompt_str = prompt_str

        self.end_flag = False  # end()が一度でも呼ばれると True

    def main(self):
        """Main."""
        self.__log.debug("")
        try:
            if self.start():
                self.loop()
        finally:
            self.end()

    def start(self) -> bool:
        """Start.
        **TO BE OVERRIDE**

        Returns:
            ret (bool)
        """
        return True

    def end(self):
        """End.
        **TO BE OVERRIDE**
        """
        self.__log.debug("end_flag=%s", self.end_flag)
        if self.end_flag:
            return

        self.end_flag = True
        self.__log.debug("done")

    def input_data(self) -> str:
        """Key input.
        **TO BE OVERRIDE**
        """
        return input(self.prompt_str)

    def parse_instr(self, instr: str) -> dict:
        """Parse input string.
        **TO BE OVERRIDE**

        Args:
            instr (str): 入力された文字列

        Returns:
            parsed_data (dict):
                {
                    "data": (Any)
                    "status": 0  # OK
                }
        """
        self.__log.debug("instr=%a", instr)

        instr = instr.strip()

        parsed_data = {"data": instr, "status": self.RESULT_STATUS["OK"]}
        return parsed_data

    def handle(self, parsed_data: dict) -> dict:
        """handle parsed data.
        **TO BE OVERRIDE**

        Args:
            parsed_data (dict):

        Returns:
            result (dict):
                {"data": "", "status": self.RESULT_STATUS[?]}
        """
        self.__log.debug("parsed_data=%s", parsed_data)
        if parsed_data.get("status") != self.RESULT_STATUS["OK"]:
            self.__log.warning("Invalid parsed_data: %s", parsed_data)
            result_data = {
                "data": f"Invalid parsed_data: {parsed_data}",
                "status": self.RESULT_STATUS["ERR"],
            }
            return result_data

        data = parsed_data.get("data")
        result = data  # result = something(data)

        result_data = {"data": result, "status": self.RESULT_STATUS["OK"]}
        if isinstance(data, str) and data.lower() in self.CMD_EXIT:
            result_data["status"] = self.RESULT_STATUS["END"]
        self.__log.debug("result_data=%s", result_data)
        return result_data

    def output_result(self, result_data: dict):
        """Output result."""
        data = result_data.get("data")
        status = result_data.get("status")

        if status == self.RESULT_STATUS["OK"]:
            print(f"result.data> {data}")
        else:
            print(f"ERROR:{status}> {data}")

    def loop(self):
        """loop"""
        self.__log.debug("")
        try:
            while True:
                try:
                    instr = self.input_data()
                    self.__log.debug("instr=%a", instr)
                except EOFError as _e:
                    # print("[EOF]")
                    self.__log.debug(errmsg(_e))
                    break

                # parse
                parsed_data = self.parse_instr(instr)
                self.__log.debug("parsed_data=%s", parsed_data)

                parsed_status = parsed_data.get("status")
                self.__log.debug("parsed_status=%s", parsed_status)

                if parsed_status == self.RESULT_STATUS["END"]:
                    self.__log.warning(parsed_data)
                    raise EOFError(parsed_data)

                if parsed_status != self.RESULT_STATUS["OK"]:
                    self.__log.warning(
                        f"parse error: {parsed_data.get('status')}"
                    )
                    continue

                result_data = {
                    "data": None,
                    "status": self.RESULT_STATUS["ERR"],
                }
                try:
                    # handle and get result
                    result_data = self.handle(parsed_data)
                    self.__log.debug("result_data=%s", result_data)

                    if result_data.get("status") == self.RESULT_STATUS["END"]:
                        raise EOFError(f"{result_data.get('data')}")

                    # output result
                    self.output_result(result_data)

                except EOFError as _e:
                    msg = errmsg(_e)
                    self.__log.warning(msg)
                    raise _e

                except Exception as _e:
                    msg = errmsg(_e)
                    self.__log.warning(msg)

        except KeyboardInterrupt as _e:
            print("^C [Interrupt]")
            self.__log.debug(errmsg(_e))


class CliWithHistory(CliBase):
    """CLI with history"""

    HIST_LEN = 500

    def __init__(
        self,
        prompt_str: str = CliBase.PROMPT_STR,
        history_file: str = "",
        debug=False,
    ):
        """Contractor."""
        super().__init__(prompt_str, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("history_file=%a", history_file)

        self.history_file = history_file

    def start(self) -> bool:
        """Start.
        **TO BE OVERRIDE**

        Returns:
            ret (bool)
        """
        # init history
        if self.history_file:
            self.history_file = os.path.expanduser(
                os.path.expandvars(self.history_file)
            )
            self.__log.debug("history_file=%a", self.history_file)

            try:
                readline.read_history_file(self.history_file)
                readline.set_history_length(self.HIST_LEN)
                self.__log.debug("hist_len=%s", readline.get_history_length())
                self.__log.debug(
                    "cur_hist_len=%s", readline.get_current_history_length()
                )
            except FileNotFoundError:
                self.__log.debug("no history file: %s", self.history_file)
            except OSError:
                self.__log.warning(
                    "invalid history file .. remove: %s", self.history_file
                )
                # ヒストリーファイルが壊れていると思われるので削除する。
                os.remove(self.history_file)
            except Exception as _e:
                self.__log.error(errmsg(_e))

        return True

    def end(self):
        """End.
        **TO BE OVERRIDE**
        """
        self.__log.debug("end_flag=%s", self.end_flag)
        if self.end_flag:
            return

        if self.history_file:
            self.__log.debug("save history: %s", self.history_file)
            try:
                readline.write_history_file(self.history_file)
            except Exception as _e:
                self.__log.error(f"{self.history_file!r}: {errmsg(_e)}")

        super().end()


class ScriptRunner(CliBase):
    """Script Runner."""

    def __init__(self, script_file, debug=False):
        super().__init__("", debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, debug=self.__debug)
        self.__log.debug("script_file=%a", script_file)

        self.script_file = script_file
        self.script_f = None

    def start(self):
        """Start."""
        # init script_file
        self.script_file = os.path.expanduser(
            os.path.expandvars(self.script_file)
        )
        self.__log.debug("script_file=%a", self.script_file)

        try:
            self.script_f = open(self.script_file, "r", encoding="utf-8")
        except Exception as _e:
            self.script_f = None
            msg = errmsg(_e)
            self.__log.error(msg)
            return False

        return True

    def end(self):
        """End."""
        self.__log.debug("end_flag=%s", self.end_flag)
        if self.end_flag:
            return

        if self.script_f:
            self.script_f.close()

        super().end()

    def input_data(self) -> str:
        """Read line."""
        if self.script_f:
            instr = self.script_f.readline()
            self.__log.debug("instr=%a(%s)", instr, type(instr).__name__)
            if instr:
                return instr
        raise EOFError


class OneKeyCli(CliBase):
    """One key CLI"""

    KEY_EOF = "\x04"
    CMD_EXIT = [
        KEY_EOF,
        "Q",
        "q",
    ]

    def __init__(self, prompt_str="> ", debug=False):
        super().__init__(prompt_str, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, debug=self.__debug)
        self.__log.debug("")

        self.term = blessed.Terminal()

    def input_data(self) -> str:
        """Read line."""
        instr = ""
        with self.term.cbreak():
            if self.prompt_str:
                print(self.prompt_str, end="", flush=True)
            instr = self.term.inkey()

            if instr.is_sequence:
                instr = instr.name
            else:
                instr = str(instr)
            self.__log.debug("instr=%a(%s)", instr, type(instr).__name__)
            print(f"{instr!r}")

            if instr in self.CMD_EXIT:
                raise EOFError

        if instr is None:
            instr = ""
        return instr
