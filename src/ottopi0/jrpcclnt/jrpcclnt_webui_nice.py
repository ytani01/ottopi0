#
# (c) 2025 Yoichi Tanibayashi
#
from datetime import datetime
from typing import Optional

from nicegui import ui

from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import get_logger
from .jrpcclnt import JrpcClient


class JrpcClntWebUiNice:
    def __init__(self, jrpc_url: str, webui_port: int, debug: bool = False):
        self.jrpc_url = jrpc_url
        self.webui_port = webui_port
        self.debug = debug
        self.logger = get_logger(self.__class__.__name__, self.debug)

        self.conf = ConfFile(debug=self.debug).conf
        self.funcs = self.conf.servo.funcs
        self.cmd_prefix = self.funcs.get("_prefix", "")

        self.cslib = CmdStrLib(debug=self.debug)

        # Load commands from config (Priority: [jrpc.client.webui.buttons] > (No Default))
        self.btn_conf = (
            self.conf.get("jrpc", {})
            .get("client", {})
            .get("webui", {})
            .get("buttons", {})
        )

        self.cmd_forward = self._mk_cmd(self.btn_conf.get("forward"))
        self.cmd_backward = self._mk_cmd(self.btn_conf.get("backward"))
        self.cmd_left = self._mk_cmd(self.btn_conf.get("left"))
        self.cmd_right = self._mk_cmd(self.btn_conf.get("right"))
        self.cmd_stop = self._mk_cmd(self.btn_conf.get("stop"))

        self.jrpc_client = JrpcClient(self.jrpc_url, debug=self.debug)

        # Log container
        self.log_container: Optional[ui.column] = None

    def _mk_cmd(self, cmd_str: str) -> str:
        """Add prefix and expand command string."""
        if not cmd_str:
            return ""
        full_cmd = f"{self.cmd_prefix} {cmd_str}"
        return self.cslib.expand_func(full_cmd)

    def send_cmd(self, cmd: str):
        """Send command to jrpc server."""
        if not cmd:
            self.log_message("No command configured for this button.")
            return

        self.log_message(f"Sending: {cmd}")
        try:
            # Re-initialize client if URL changed (simple approach)
            if self.jrpc_client.url != self.jrpc_url:
                self.jrpc_client = JrpcClient(self.jrpc_url, debug=self.debug)

            res = self.jrpc_client.jrpc_call(cmd)
            self.log_message(f"Result: {res}")
        except Exception as e:
            self.log_message(f"Error: {e}")

    def send_custom_cmd(self, cmd: str):
        """Send custom command entered by user."""
        if not cmd or not cmd.strip():
            self.log_message("Please enter a command.")
            return

        # Expand the custom command using CmdStrLib
        expanded_cmd = self.cslib.expand_func(cmd.strip())
        self.send_cmd(expanded_cmd)

    def log_message(self, msg: str):
        """Add message to log."""
        ts = datetime.now().strftime("%H:%M:%S")
        if self.log_container:
            with self.log_container:
                ui.label(f"[{ts}] {msg}")
        self.logger.info(msg)

    def build_ui(self):
        """Build the NiceGUI UI."""
        ui.colors(primary="#007bff", secondary="#6c757d", accent="#17a2b8")

        with ui.header().classes("items-center justify-between"):
            ui.label("Robot Remote Controller (NiceGUI)").classes("text-h6")

        with ui.column().classes("w-full items-center gap-4 p-4"):
            # Config Panel
            with ui.card().classes("w-full max-w-lg"):
                ui.label("Configuration").classes("text-lg font-bold mb-2")
                ui.input("Target URL", value=self.jrpc_url).bind_value(
                    self, "jrpc_url"
                ).classes("w-full")

            # Control Panel
            with ui.card().classes("w-full max-w-lg items-center"):
                ui.label("Control").classes("text-lg font-bold mb-4")

                with ui.grid(columns=3).classes("gap-4"):
                    # Row 1
                    ui.label("")  # Empty
                    ui.button(
                        on_click=lambda: self.send_cmd(self.cmd_forward)
                    ).props("icon=arrow_upward round size=xl")
                    ui.label("")  # Empty

                    # Row 2
                    ui.button(
                        on_click=lambda: self.send_cmd(self.cmd_left)
                    ).props("icon=arrow_back round size=xl")
                    ui.button(
                        on_click=lambda: self.send_cmd(self.cmd_stop)
                    ).props("icon=stop round color=red size=xl")
                    ui.button(
                        on_click=lambda: self.send_cmd(self.cmd_right)
                    ).props("icon=arrow_forward round size=xl")

                    # Row 3
                    ui.label("")  # Empty
                    ui.button(
                        on_click=lambda: self.send_cmd(self.cmd_backward)
                    ).props("icon=arrow_downward round size=xl")
                    ui.label("")  # Empty

            # Custom Command Panel
            with ui.card().classes("w-full max-w-lg"):
                ui.label("Custom Command").classes("text-lg font-bold mb-2")
                with ui.row().classes("w-full gap-2"):
                    custom_input = ui.input(
                        placeholder="Enter custom command..."
                    ).classes("flex-grow")
                    ui.button(
                        "Send",
                        on_click=lambda: self.send_custom_cmd(
                            custom_input.value
                        ),
                    ).props("color=primary")

            # Log Panel
            with ui.card().classes("w-full max-w-lg h-48 overflow-auto"):
                ui.label("Logs").classes(
                    "text-lg font-bold mb-2 sticky top-0 bg-white z-10"
                )
                self.log_container = ui.column().classes("w-full")

    def run(self):
        """Start the application."""

        # NiceGUI requires UI building to happen within the page context
        # when called from CLI/module context
        @ui.page("/")
        def index():
            self.build_ui()

        self.logger.info(f"Starting NiceGUI on port {self.webui_port}")
        ui.run(
            host="0.0.0.0",
            port=self.webui_port,
            title="Ottopi0 Controller",
            reload=False,
            show=False,
        )
