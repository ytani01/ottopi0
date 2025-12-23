# テストスイート改善計画 2 (Plan02.md)

`tests/` ディレクトリの再レビューに基づき、以下の追加改善を実施します。

## 1. `conftest.py` の `unittest.mock` から `pytest-mock` への移行

`tests/conftest.py` 内のフィクスチャが現在 `unittest.mock.patch` をコンテキストマネージャとして使用しています。これを `pytest-mock` の `mocker` フィクスチャを使用する形にリファクタリングし、他のテストファイルと整合させます。

**変更内容:**
- `mock_cli_app`, `mock_bt_app`, `mock_webui_app` フィクスチャを `mocker.patch` を使用するように変更。

## 2. CLIテストのクラス名変更

一部のCLIテストファイルで、古い命名規則のクラス名が残っているため、これを修正します。

**対象と変更案:**
- `tests/test_11_cli_cmd.py`: `TestCliJrpcClntCli` -> `TestCliCmd`
- `tests/test_12_cli_bt.py`: `TestCliJrpcClntBt` -> `TestCliBt`

## 3. `test_10_cli_svr.py` のリファクタリング

このファイルも `unittest.mock` を使用しているため、`pytest-mock` を使用するように書き換えます。

**変更内容:**
- `mock_uvicorn` フィクスチャを `mocker.patch` を使用するように変更。
- `TestCliSvr` クラス内のテストメソッドで `mocker` が適切に機能するように調整。

## 4. 実行計画

1.  `tests/conftest.py` を修正。
2.  `tests/test_11_cli_cmd.py` と `tests/test_12_cli_bt.py` のクラス名を修正。
3.  `tests/test_10_cli_svr.py` をリファクタリング。
4.  全テストを実行し (`mise run test`)、変更の影響がないか確認。
