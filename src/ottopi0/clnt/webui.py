#
# (c) 2025 Yoichi Tanibayashi
#
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..common.cmdstr_lib import CmdStrLib
from ..common.conf_file import ConfFile
from ..utils.mylogger import get_logger
from .clnt import Client


class CommandRequest(BaseModel):
    cmd: str
    jrpc_url: Optional[str] = None


class WebUI:
    """WebUI for Robot Control."""

    def __init__(self, jrpc_url: str, webui_port: int, debug: bool = False):
        self.jrpc_url = jrpc_url
        self.webui_port = webui_port
        self.debug = debug
        self.logger = get_logger(self.__class__.__name__, self.debug)

        self.conf = ConfFile(debug=self.debug).conf
        self.funcs = self.conf.servo.funcs
        self.cmd_prefix = self.funcs.get("_prefix", "")

        self.cslib = CmdStrLib(debug=self.debug)

        # Load commands from config
        # Priority: [jrpc.client.webui.buttons] > (No Default)
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

        self.logger.info(
            f"Commands loaded: F={self.cmd_forward}, B={
                self.cmd_backward
            }, L={self.cmd_left}, R={self.cmd_right}, S={self.cmd_stop}"
        )

        self.jrpc_client = Client(self.jrpc_url, debug=self.debug)
        self.app = FastAPI()

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if os.path.exists(static_dir):
            self.app.mount(
                "/static", StaticFiles(directory=static_dir), name="static"
            )
        else:
            self.logger.warning(f"Static directory not found: {static_dir}")

        self.setup_routes()

    def _mk_cmd(self, cmd_str: str) -> str:
        """Add prefix and expand command string."""
        if not cmd_str:
            return ""
        full_cmd = f"{self.cmd_prefix} {cmd_str}"
        return self.cslib.expand_func(full_cmd)

    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            default_url = (
                self.jrpc_url
            )  # Use the current initialized URL as default

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Robot Controller</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }}
                    .config-panel {{
                        margin-bottom: 20px;
                        padding: 10px;
                        background: #fff;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .control-panel {{
                        display: grid;
                        grid-template-areas:
                            ". forward ."
                            "left stop right"
                            ". backward .";
                        gap: 15px;
                    }}
                    button {{
                        padding: 20px;
                        font-size: 18px;
                        cursor: pointer;
                        border: none;
                        border-radius: 15px;
                        background-color: #007bff;
                        color: white;
                        transition: background-color 0.3s;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 100px;
                        height: 100px;
                    }}
                    button:active {{
                        background-color: #0056b3;
                    }}
                    button.stop {{
                        background-color: #dc3545;
                        grid-area: stop;
                    }}
                    button.stop:active {{
                        background-color: #bd2130;
                    }}
                    button.forward {{ grid-area: forward; }}
                    button.backward {{ grid-area: backward; }}
                    button.left {{ grid-area: left; }}
                    button.right {{ grid-area: right; }}
                    
                    .icon {{
                        width: 48px;
                        height: 48px;
                        pointer-events: none;
                    }}
                    
                    #status {{
                        margin-top: 20px;
                        font-weight: bold;
                        color: #333;
                    }}
                    .custom-cmd {{
                        margin-top: 30px;
                        display: flex;
                        gap: 10px;
                    }}
                    input[type="text"] {{
                        padding: 10px;
                        font-size: 16px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                    }}
                    .url-input {{
                        width: 300px;
                    }}
                </style>
            </head>
            <body>
                <h1>Robot Remote Controller</h1>

                <div class="config-panel">
                    <label for="targetUrl">Target URL: </label>
                    <input type="text" id="targetUrl" class="url-input" value="{default_url}">
                </div>

                <div class="control-panel">
                    <button class="forward" onclick="sendCommand('{self.cmd_forward}')">
                        <img src="/static/forward.svg" alt="Forward" class="icon">
                    </button>
                    <button class="left" onclick="sendCommand('{self.cmd_left}')">
                        <img src="/static/left.svg" alt="Left" class="icon">
                    </button>
                    <button class="stop" onclick="sendCommand('{self.cmd_stop}')">
                        <img src="/static/stop.svg" alt="Stop" class="icon">
                    </button>
                    <button class="right" onclick="sendCommand('{self.cmd_right}')">
                        <img src="/static/right.svg" alt="Right" class="icon">
                    </button>
                    <button class="backward" onclick="sendCommand('{self.cmd_backward}')">
                        <img src="/static/backward.svg" alt="Backward" class="icon">
                    </button>
                </div>

                <div class="custom-cmd">
                    <input type="text" id="customCmdInput" placeholder="Enter custom command...">
                    <button onclick="sendCustomCommand()">Send</button>
                </div>

                <div id="status">Ready</div>

                <script>
                    async function sendCommand(cmd) {{
                        const statusDiv = document.getElementById('status');
                        const targetUrl = document.getElementById('targetUrl').value;

                        statusDiv.innerText = 'Sending: ' + cmd + ' to ' + targetUrl + ' ...';
                        try {{
                            const response = await fetch('/api/cmd', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify({{ cmd: cmd, jrpc_url: targetUrl }}),
                            }});
                            const data = await response.json();
                            console.log(data);
                            statusDiv.innerText = 'Result: ' + \
                                JSON.stringify(data.result);
                        }} catch (error) {{
                            console.error('Error:', error);
                            statusDiv.innerText = 'Error: ' + error;
                        }}
                    }}

                    function sendCustomCommand() {{
                        const cmd = document.getElementById('customCmdInput').value;
                        if (cmd) {{
                            sendCommand(cmd);
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            return html_content

        @self.app.post("/api/cmd")
        async def send_cmd(request: CommandRequest):
            self.logger.info(
                f"Received web command: {request.cmd}, url={request.jrpc_url}"
            )

            # Use dynamic URL if provided and different from current
            current_client = self.jrpc_client
            if request.jrpc_url and request.jrpc_url != self.jrpc_url:
                # Update the default URL and client if it changed permanently?
                # Or just use a temporary client?
                # For now, let's create a temporary client to avoid side effects if we want to support multiple users (though this is single threaded mostly)
                # But sticking to one state is simpler for "configuration".
                # Let's update the instance variable so it persists for the session (simple approach).
                self.jrpc_url = request.jrpc_url
                self.jrpc_client = Client(self.jrpc_url, debug=self.debug)
                current_client = self.jrpc_client

            result = current_client.jrpc_call(request.cmd)
            return {"status": "ok", "result": result}

    def run(self):
        self.logger.info(f"Starting WebUI on port {self.webui_port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.webui_port)
