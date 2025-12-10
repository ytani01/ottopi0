from unittest import mock

import pytest
from click.testing import CliRunner


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


@pytest.fixture
def cli_runner():
    """`CliRunner`のインスタンスを提供するフィクスチャ。"""
    return CliRunner()


def assert_cli_result(
    result,
    exit_code=0,
    expected_output_fragments=None,
    unexpected_output_fragments=None,
):
    """CLIコマンドの結果をアサートするヘルパー関数。

    Args:
        result: `CliRunner.invoke`の戻り値。
        exit_code: 期待される終了コード。デフォルトは0。
        expected_output_fragments: 期待される出力フラグメントのリスト。
        unexpected_output_fragments: 予期しない出力フラグメントのリスト。
    """
    assert result.exit_code == exit_code, (
        f"Expected exit code {exit_code}, but got {result.exit_code}.\n"
        f"Output: {result.output}"
    )

    if expected_output_fragments:
        for fragment in expected_output_fragments:
            assert fragment in result.output, (
                f"Expected '{fragment}' in output, but not found.\n"
                f"Output: {result.output}"
            )

    if unexpected_output_fragments:
        for fragment in unexpected_output_fragments:
            assert fragment not in result.output, (
                f"Unexpected '{fragment}' found in output.\n"
                f"Output: {result.output}"
            )
