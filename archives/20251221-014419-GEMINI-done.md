# OttoPi0 プロジェクト分析

## プロジェクト概要

`OttoPi0` プロジェクトは、Otto DIY に似た二足歩行ロボットのための Python ベースの制御システムで、Raspberry Pi Zero 2W 上で動作するように設計されています。このプロジェクトはクライアント・サーバーアーキテクチャを採用しています。

-   **サーバー**: Raspberry Pi 上で動作する FastAPI ウェブサーバーです。ロボットを制御するための JSON-RPC 2.0 API を公開しています。`pigpio` ライブラリを使用して、ロボットのハードウェア、特にサーボと直接インターフェースします。サーバーは、高レベルのコマンドを低レベルのサーボ動作に変換する役割を担っています。

-   **クライアント**: いくつかのクライアントが JSON-RPC サーバーに接続してコマンドを送信できます。
    -   コマンドラインインターフェース (`cmd`)。
    -   ゲームパッド (例: 8BitDo Micro) を使用したリモートコントロール用の Bluetooth クライアント (`bt`)。
    -   NiceGUI で構築されたウェブベースの UI (`nicegui`)。
    -   VL53L0X 距離センサーを使用する自律モードクライアント (`auto`)。

-   **コマンドシステム**: このプロジェクトは柔軟なコマンドシステムを使用しており、ダンスの動きのような複雑なコマンドシーケンスを TOML 設定ファイル内の関数として定義できます。コマンド文字列ライブラリ (`cmdstr_lib`) は、これらの関数をサーバーに送信する前に一連のプリミティブコマンドに展開します。

-   **技術要素**:
    -   **バックエンド**: Python, FastAPI, Uvicorn, JSON-RPC.
    -   **フロントエンド**: NiceGUI.
    -   **ハードウェア連携**: `pigpio`, `pi0servo`, `pibtinput`, `vl53l0x-pigpio`.
    -   **CLI**: `click`.
    -   **設定**: `dynaconf` (TOML ファイルを使用).
    -   **プロジェクト管理**: `mise`, `uv`.

## ビルドと実行

このプロジェクトは、ツールバージョン管理に `mise` を、Python 環境とパッケージ管理に `uv` を使用して管理されています。

### インストール

1.  **`mise` と `uv` のインストール**:
    ```bash
    # mise をインストール
    curl https://mise.run | sh
    eval "$(~/.local/bin/mise activate bash)" # または zsh

    # uv と python をインストール
    mise use -g uv@latest
    mise use -g python@latest
    ```

2.  **リポジトリのクローンとビルド**:
    ```bash
    for p in pi0servo pi0disp pibtinput vl53l0x_pigpio ottopi0; do git clone https://github.com/ytani01/$p; mise trust $p/mise.toml; done

    cd ottopi0
    cp ottopi0.toml.sample ~/ottopi0.toml
    mise run build
    ```

### サーバーの実行

メインのロボット制御サーバーは次のように起動します。

```bash
uv run ottopi0 svr
```

### クライアントの実行

クライアントは実行中のサーバーに接続します。

-   **コマンドラインクライアント**:
    ```bash
    uv run ottopi0 cmd
    ```

-   **Bluetooth クライアント**:
    ```bash
    uv run ottopi0 bt [bt_device_keyword]
    ```

-   **NiceGUI ウェブ UI**:
    ```bash
    uv run ottopi0 webui
    ```

## 開発規約

-   **パッケージ管理**: プロジェクトは Python の依存関係管理に `uv` を使用しています。依存関係は `pyproject.toml` に記載されています。ローカルの依存関係は `[tool.uv.sources]` セクションで指定されます。
-   **テスト**: テストは `pytest` を使用して記述されています。テストファイルは `tests/` ディレクトリにあります。テストを実行するには、以下を使用します。
    ```bash
    uv run pytest
    ```
-   **リンティングと型チェック**: プロジェクトはリンティングに `ruff`、静的型チェックに `mypy` を使用しています。これらのツールの設定は `pyproject.toml` にあります。
-   **設定**: アプリケーションの設定は `dynaconf` によって処理されます。メインの設定ファイルは `~/ottopi0.toml` であり、`ottopi0.toml.sample` のコピーです。このファイルは、サーボピン、コマンドシーケンス、クライアント/サーバー設定を定義します。
-   **CLI**: コマンドラインインターフェースは `click` で構築されており、`src/ottopi0/__main__.py` で定義されています。