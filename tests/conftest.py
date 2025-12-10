from unittest import mock

import pytest


@pytest.fixture
def mock_cli_app():
    """ottopi0.clnt.cmd.Cmd をモックするフィクスチャ。"""
    with mock.patch("ottopi0.clnt.cmd.Cmd") as MockApp:
        yield MockApp


@pytest.fixture
def mock_bt_app():
    """ottopi0.clnt.bt.Bt をモックするフィクスチャ。"""
    with mock.patch("ottopi0.clnt.bt.Bt") as MockApp:
        yield MockApp


@pytest.fixture
def mock_webui_app():
    """ottopi0.clnt.webui.WebUI をモックするフィクスチャ。"""
    with mock.patch("ottopi0.clnt.webui.WebUI") as MockApp:
        yield MockApp


def cli_url_builder(host, port, apipath):
    """CLIコマンドで使用するURLを構築するヘルパー関数。"""
    return f"http://{host}:{port}{apipath}"
