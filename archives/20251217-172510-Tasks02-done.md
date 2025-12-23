# テストスイート改善タスクリスト (Tasks02.md)

Plan02.mdに基づくリファクタリング作業のチェックリストです。

- [x] **Task 1: `tests/conftest.py` のリファクタリング**
  - [x] `mock_cli_app` フィクスチャを `mocker.patch` を使用するように変更
  - [x] `mock_bt_app` フィクスチャを `mocker.patch` を使用するように変更
  - [x] `mock_webui_app` フィクスチャを `mocker.patch` を使用するように変更
  - [x] 不要になった `unittest.mock` のインポートを削除

- [x] **Task 2: CLIテストのクラス名変更**
  - [x] `tests/test_11_cli_cmd.py`: クラス名を `TestCliJrpcClntCli` から `TestCliCmd` に変更
  - [x] `tests/test_12_cli_bt.py`: クラス名を `TestCliJrpcClntBt` から `TestCliBt` に変更

- [x] **Task 3: `tests/test_10_cli_svr.py` のリファクタリング**
  - [x] `mock_uvicorn` フィクスチャを `mocker.patch` を使用するように変更
  - [x] テストメソッド内でのモック参照方法を調整
  - [x] 不要になった `unittest.mock` のインポートを削除

- [x] **Task 4: 全体動作確認**
  - [x] `mise run test` を実行し、全てのテストが通過することを確認
  - [x] リンター (`ruff`, `mypy`) のエラーがないことを確認
