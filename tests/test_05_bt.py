#
# (c) 2025 Yoichi Tanibayashi
#
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from ottopi0.clnt.bt import Bt


class TestJrpcClntBt:
    """jrpcclnt_bt.py内のJrpcClntBtのテストクラス。"""

    @pytest.fixture
    def mock_deps(self):
        """依存関係をモック: PiBtInput, JrpcClient, CmdStrLib, ConfFile。"""
        with (
            patch("ottopi0.clnt.bt.PiBtInput") as MockPiBtInput,
            patch("ottopi0.clnt.bt.Client") as MockJrpcClient,
            patch("ottopi0.clnt.bt.CmdStrLib") as MockCmdStrLib,
            patch("ottopi0.clnt.bt.ConfFile") as MockConfFile,
        ):
            # モックConfFileのセットアップ
            mock_conf_instance = MockConfFile.return_value
            mock_conf = MagicMock()
            mock_conf_instance.conf = mock_conf

            # デフォルト設定構造
            mock_conf.servo.funcs = {"_prefix": "prefix:"}
            mock_conf.jrpc.client.bluetooth.get.return_value = {}  # デフォルトは空のキー

            # モックCmdStrLibのセットアップ
            mock_cslib_instance = MockCmdStrLib.return_value
            # 簡略化のために入力文字列を展開されたものとして返す、または必要に応じて変更
            mock_cslib_instance.expand_func.side_effect = lambda x: x

            yield {
                "PiBtInput": MockPiBtInput,
                "JrpcClient": MockJrpcClient,
                "CmdStrLib": MockCmdStrLib,
                "ConfFile": MockConfFile,
                "conf": mock_conf,
                "cslib": mock_cslib_instance,
            }

    def test_mk_keymap_normalization(self, mock_deps):
        """mk_keymapが 'KEY_B-KEY_A' を 'KEY_A-KEY_B' に正規化することをテスト。"""
        # 準備
        keys_config = {
            "KEY_A": "cmd_a",
            "KEY_B-KEY_A": "cmd_ab",  # 設定でソートされていない
            "KEY_X-KEY_Y-KEY_Z": "cmd_xyz",
        }
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config

        # Act
        # JrpcClntBtを初期化 (mk_keymapが呼ばれる)
        clnt = Bt("dummy_keyword", "http://dummy")

        # アサート
        # キーがself.keymapで正規化されていることを確認
        # プレフィックスは "prefix:"
        assert "KEY_A" in clnt.keymap
        assert clnt.keymap["KEY_A"] == "prefix: cmd_a"

        # "KEY_B-KEY_A" は "KEY_A-KEY_B" として保存されるべき
        assert "KEY_A-KEY_B" in clnt.keymap
        assert "KEY_B-KEY_A" not in clnt.keymap
        assert clnt.keymap["KEY_A-KEY_B"] == "prefix: cmd_ab"

        # 3つのキー
        assert "KEY_X-KEY_Y-KEY_Z" in clnt.keymap

    def test_cb_ev_single_key(self, mock_deps):
        """単一キー押下でのコールバックをテスト。"""
        # 準備
        keys_config = {"KEY_A": "cmd_a"}
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = Bt("dummy_keyword", "http://dummy")

        # キーイベントをモック
        key_name = "KEY_A"

        # ダウン
        # (ロジックでは特別に処理されないが、keys["up"]/["hold"]をチェック)
        key_state = 1

        # PiBtInput.KEY["up"]は通常0、
        # "hold"は2。1がダウンと仮定。
        # "up"または"hold"が返されないことを確認する必要がある。
        # PiBtInput.KEYの値を知る必要がある。
        # PiBtInputをモックしたので、
        # コード内のクラス属性アクセスをチェック:
        # if key_state == PiBtInput.KEY["up"]:
        # モックされたPiBtInput.KEYディクショナリを設定する必要がある。
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        onkeys = {"KEY_A": 123}  # dict of key:keycode

        # 実行
        clnt.cb_ev(key_name, key_state, onkeys)

        # アサート
        # マップされたコマンドでjrpc_callが呼ばれるはず
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_a"
        )

    def test_cb_ev_chord(self, mock_deps):
        """同時キー押下 (コード) でのコールバックをテスト。"""
        # 準備
        keys_config = {
            "KEY_A": "cmd_a",
            "KEY_B": "cmd_b",
            # 設定内の正規化されたキーは、コードも正規化することを意味する
            # B-Aと書かれている場合
            "KEY_A-KEY_B": "cmd_ab",
        }
        # 設定でもB-Aを提供して、そこで正規化が機能することを確認してみましょう
        keys_config["KEY_D-KEY_C"] = "cmd_cd"

        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = Bt("dummy_keyword", "http://dummy")
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        # ケース1: AとBが押された
        onkeys = {
            "KEY_B": 1,
            "KEY_A": 1,
        }  # ディクショナリ内の順序は重要ではないはず
        clnt.cb_ev(
            "KEY_B", 1, onkeys
        )  # Aがすでに押されている間に、Bがダウンでトリガーされる

        # アサート
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_ab"
        )

        # ケース2: CとDが押された (設定にはD-Cがある)
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).reset_mock()
        onkeys = {"KEY_C": 1, "KEY_D": 1}
        clnt.cb_ev("KEY_D", 1, onkeys)

        # アサート
        # 設定内の "KEY_D-KEY_C" -> keymapでは "KEY_C-KEY_D" に正規化
        # onkeys "C", "D" -> ソート済み "C", "D" -> 結合済み "KEY_C-KEY_D"
        # keymap["KEY_C-KEY_D"] -> "prefix: cmd_cd"
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_called_with(
            "prefix: cmd_cd"
        )

    def test_cb_ev_no_match(self, mock_deps):
        """一致するキー/コードがないコールバックをテスト。"""
        keys_config = {"KEY_A": "cmd_a"}
        mock_deps["conf"].jrpc.client.bluetooth.get.return_value = keys_config
        clnt = Bt("dummy_keyword", "http://dummy")
        mock_deps["PiBtInput"].KEY = {"up": 0, "hold": 2, "down": 1}

        # Zを押す (マップされていない)
        onkeys = {"KEY_Z": 1}
        clnt.cb_ev("KEY_Z", 1, onkeys)

        # アサート
        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_not_called()

        # A+Bを押す (Aのみマップされ、コードはマップされていない)
        # 現在のロジック: _current_combo = "KEY_A-KEY_B"。
        # 見つからなかった場合、単一キー処理にフォールバックするか？
        # ユーザーは単一キーのフォールバックをコメントアウトした！
        # フォールバックがコメントアウトされている場合:
        # _cmd_str = keymap.get("KEY_A-KEY_B") -> None
        # jrpc_callは呼び出されない。

        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).reset_mock()
        onkeys = {"KEY_A": 1, "KEY_B": 1}
        clnt.cb_ev("KEY_B", 1, onkeys)

        cast(MagicMock, clnt.jrpc_clnt.jrpc_call).assert_not_called()
