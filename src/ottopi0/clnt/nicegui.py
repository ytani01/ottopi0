#
# (c) 2025 Yoichi Tanibayashi
#
import os
import signal
import sys
from datetime import datetime
from typing import Optional

from nicegui import ui

from .. import ENVNAME_DEBUG, PKGNAME
from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import get_logger
from .clnt import Client

# Environment variable names for NiceGUI configuration
ENVNAME_NICEGUI_URL = f"{PKGNAME}_NICEGUI_URL"
ENVNAME_NICEGUI_PORT = f"{PKGNAME}_NICEGUI_PORT"


class NiceGUI:
    def __init__(self, jrpc_url: str, nicegui_port: int, debug: bool = False):
        self.jrpc_url = jrpc_url
        self.nicegui_port = nicegui_port
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
            .get("nicegui", {})
            .get("buttons", {})
        )

        self.cmd_forward = self._mk_cmd(self.btn_conf.get("forward"))
        self.cmd_backward = self._mk_cmd(self.btn_conf.get("backward"))
        self.cmd_left = self._mk_cmd(self.btn_conf.get("left"))
        self.cmd_right = self._mk_cmd(self.btn_conf.get("right"))
        self.cmd_stop = self._mk_cmd(self.btn_conf.get("stop"))

        self.jrpc_client = Client(self.jrpc_url, debug=self.debug)

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
                self.jrpc_client = Client(self.jrpc_url, debug=self.debug)

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
                ui.label("Robot Server URL").classes("text-lg font-bold mb-2")
                ui.input(value=self.jrpc_url).bind_value(
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

            # Custom Command Panel (Collapsible)
            with ui.expansion("Custom Command", icon="terminal").classes(
                "w-full max-w-lg"
            ):
                with ui.row().classes("w-full gap-2 p-2"):
                    custom_input = ui.input(
                        placeholder="Enter custom command..."
                    ).classes("flex-grow")
                    ui.button(
                        "Send",
                        on_click=lambda: self.send_custom_cmd(
                            custom_input.value
                        ),
                    ).props("color=primary")

            # Log Panel (Collapsible)
            with ui.expansion("Logs", icon="description", value=True).classes(
                "w-full max-w-lg"
            ):
                with ui.scroll_area().classes("h-48 w-full p-2"):
                    self.log_container = ui.column().classes("w-full")

    def run(self):
        """Start the application."""

        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.logger.info("Received interrupt signal, shutting down...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # NiceGUI requires UI building to happen within the page context
        # when called from CLI/module context
        @ui.page("/")
        def index():
            self.build_ui()

        self.logger.info(f"Starting NiceGUI on port {self.nicegui_port}")

        # Note: reload=True requires ui.run() to be called from __main__ guard
        # Since we're called from CLI, we cannot use auto-reload
        # See: https://nicegui.io/documentation/section_configuration_deployment#auto-reload
        if self.debug:
            self.logger.warning(
                "Auto-reload is not available when running from CLI. "
                "To use auto-reload, run NiceGUI directly from a Python script."
            )

        try:
            ui.run(
                host="0.0.0.0",
                port=self.nicegui_port,
                title="Ottopi0 Controller",
                reload=False,  # Cannot use reload from CLI context
                show=False,
            )
        except KeyboardInterrupt:
            self.logger.info("Application stopped by user")
            sys.exit(0)


# Module-level setup for auto-reload support (similar to svr pattern)
def setup_app():
    """Setup NiceGUI app from environment variables for auto-reload support."""
    # Read configuration from environment variables
    jrpc_url = os.getenv(ENVNAME_NICEGUI_URL, "http://localhost:8000/api")
    nicegui_port = int(os.getenv(ENVNAME_NICEGUI_PORT, "5000"))
    debug = os.getenv(ENVNAME_DEBUG) == "1"

    logger = get_logger(__name__, debug)
    logger.debug(
        f"setup_app: url={jrpc_url}, port={nicegui_port}, debug={debug}"
    )

    # Create NiceGUI instance
    app = NiceGUI(jrpc_url, nicegui_port, debug)

    # Setup UI page
    @ui.page("/")
    def index():
        app.build_ui()

    logger.info(f"NiceGUI app configured on port {nicegui_port}")
    return app


# For auto-reload: call setup when module is loaded
if os.getenv(ENVNAME_NICEGUI_URL):
    setup_app()
