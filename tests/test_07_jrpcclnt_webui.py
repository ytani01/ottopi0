#
# (c) 2025 Yoichi Tanibayashi
#
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from ottopi0.jrpcclnt.jrpcclnt_webui import JrpcClntWebUI


class TestJrpcClntWebUI:
    @pytest.fixture
    def mock_jrpc_client(self):
        with mock.patch(
            "ottopi0.jrpcclnt.jrpcclnt_webui.JrpcClient"
        ) as MockClass:
            mock_instance = MockClass.return_value
            # Mock the method to return a dummy result
            mock_instance.jrpc_call.return_value = {"status": "success"}
            yield mock_instance

    @pytest.fixture
    def webui_app(self, mock_jrpc_client):
        # Create instance with dummy URL and port
        webui = JrpcClntWebUI("http://dummy:8080", 5000, debug=True)
        # We need to manually inject the mocked client if the constructor creates a new one
        # But since we patched the class, the constructor uses the mock class.
        # However, checking the implementation: self.jrpc_client = JrpcClient(...)
        # So it should be the mock instance.
        return webui.app

    @pytest.fixture
    def client(self, webui_app):
        return TestClient(webui_app)

    def test_root(self, client):
        """Test the root endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Robot Remote Controller" in response.text
        assert "text/html" in response.headers["content-type"]
        assert 'img src="/static/forward.svg"' in response.text

    def test_static_file(self, client):
        """Test that static files are served."""
        # Ensure the file exists (it should, as we created it)
        # But in test environment, we need to make sure the app mount points to the real directory
        # Since we use __file__ in the source, it depends on where the test runs vs source.
        # But we are running from root, and importing the module. The module's __file__ is correct.
        response = client.get("/static/forward.svg")
        assert response.status_code == 200
        assert (
            "image/svg+xml" in response.headers["content-type"]
            or "image/svg" in response.headers["content-type"]
        )

    def test_send_cmd(self, client, mock_jrpc_client):
        """Test sending a command via API."""
        cmd = "forward 0.5"
        response = client.post("/api/cmd", json={"cmd": cmd})

        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "result": {"status": "success"},
        }

        # Verify jrpc_call was called with the command
        mock_jrpc_client.jrpc_call.assert_called_with(cmd)

    def test_send_cmd_with_url(self, client, mock_jrpc_client):
        """Test sending a command with a specific target URL."""
        cmd = "stop"
        target_url = "http://new-target:9000"

        # Need to patch the class again or ensure the new instance created inside send_cmd is also mocked?
        # The implementation creates a *new* JrpcClient if the URL changes.
        # We need to ensure that *new* creation is also mocked to avoid real network calls.
        # The fixture `mock_jrpc_client` patches the class globally for the test function scope if used properly.
        # But wait, the fixture creates a mock when it yields.
        # Let's verify if subsequent calls to JrpcClient() return new mocks or the same mock.
        # MockClass.return_value is usually the SAME mock object by default unless side_effect is set.

        response = client.post(
            "/api/cmd", json={"cmd": cmd, "jrpc_url": target_url}
        )

        assert response.status_code == 200
        # The implementation should have updated self.jrpc_url
        # And called jrpc_call on the (mocked) client
        mock_jrpc_client.jrpc_call.assert_called_with(cmd)

    def test_commands_loaded(self, mock_jrpc_client):
        """Verify that commands are loaded (expanded) correctly."""
        # Using a fresh instance to avoid fixture complexity for this specific check
        # Mock ConfFile to return specific button config
        with (
            mock.patch(
                "ottopi0.jrpcclnt.jrpcclnt_webui.ConfFile"
            ) as MockConfFile,
            mock.patch(
                "ottopi0.jrpcclnt.jrpcclnt_webui.CmdStrLib"
            ) as MockCmdStrLib,
        ):
            # Setup Mock Config
            mock_conf = MockConfFile.return_value.conf

            # 1. Support conf.servo.funcs.get(...)
            mock_conf.servo.funcs = {"forward": "DEFAULT_FORWARD"}

            # 2. Support conf.get("jrpc")...
            # We mock .get() to return the dictionary structure when "jrpc" is requested
            mock_conf.get.side_effect = (
                lambda k, d=None: {
                    "client": {
                        "webui": {"buttons": {"forward": "WEBUI_FORWARD"}}
                    }
                }
                if k == "jrpc"
                else d
            )

            mock_cslib = MockCmdStrLib.return_value
            mock_cslib.expand_func.side_effect = lambda x: f"EXPANDED:{x}"

            webui = JrpcClntWebUI("http://dummy", 5000)

            # Check if expand_func was called for our configured value
            # "WEBUI_FORWARD" should be prefixed (if any) and expanded.
            # prefix defaults to ""; full_cmd = " WEBUI_FORWARD"
            assert "EXPANDED: WEBUI_FORWARD" in webui.cmd_forward

    def test_commands_missing(self, mock_jrpc_client):
        """Verify that commands are empty if not configured (no fallback)."""
        with (
            mock.patch(
                "ottopi0.jrpcclnt.jrpcclnt_webui.ConfFile"
            ) as MockConfFile,
            mock.patch("ottopi0.jrpcclnt.jrpcclnt_webui.CmdStrLib"),
        ):
            # Setup Mock Config with empty buttons
            mock_conf = MockConfFile.return_value.conf

            # 1. Support conf.servo.funcs
            mock_conf.servo.funcs = {"forward": "FALLBACK_FORWARD"}

            # 2. Support conf.get("jrpc")...
            # Return empty buttons config
            mock_conf.get.side_effect = (
                lambda k, d=None: {"client": {"webui": {"buttons": {}}}}
                if k == "jrpc"
                else d
            )

            webui = JrpcClntWebUI("http://dummy", 5000)

            # Should be empty string, not FALLBACK_FORWARD
            assert webui.cmd_forward == ""
