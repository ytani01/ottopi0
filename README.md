# OttoPi0 - ``Otto DIY`` like biped robot for Raspberry Pi

![](docs/robot-fig1.png)


## == 特徴

### Hardware

- Raspberry Pi Zero 2W
- Original PCB

### Software

- Raspberry Pi OS (bookworm)
- pigpio
- Python


## == Install

### === Raspberry Pi OS (bookworm)

**重要**: 最新版ではなく、「bookwork」にすること！


### === 基本ツールのインストール: mise, uv

**mise**: ツールや言語のバージョン管理 ＋ タスクランナー

**uv**: Pythonプロジェクト管理

``` bash
# mise のインストール
curl https://mise.run | sh

# mise の初期設定
## bashの場合
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
## zshの場合
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc

# === ここでシェルを再起動 or ターミナル再起動 or sshし直しなど ===

# uv, python のインストール
mise use -g uv@latest
mise use -g python@latest
```


### === ``ottopi0``と関連パッケージのインストールと設定

``` bash
# gitクローン
for p in pi0servo pi0disp pibtinput vl53l0x_pigpio ottopi0; do git clone https://github.com/ytani01/$p; mise trust $p/mise.toml; done

cd ottopi0
cp ottopi0.toml.sample ~
mise run build
```


## == 使用方法

### === 1. ``~/ottopi0.toml``の設定

- ピン番号の設定


### === 2. コマンドライン

``uv run ottopi0``コマンドのサブコマンド


**ロボット制御サーバー**

``` bash
uv run ottopi0 svr -h

Usage: ottopi0 svr [OPTIONS]

Options:
  -s, --servo-pins, --pins TEXT  servo pins  [default: 20-,26,19-,16]
  -i, --host TEXT                hostname or ipaddr  [default: 0.0.0.0]
  -p, --port INTEGER             port number  [default: 8000]
  -r, --reload                   reload flag
  -V, --version                  Show the version and exit.
  -d, --debug                    debug flag
  -h, --help                     Show this message and exit.
```


**コマンドライン・クライアント**

``` bash
uv run ottopi0 cmd -h

Usage: ottopi0 cmd [OPTIONS]

  JSON-RPC Client for command line interface.

Options:
  --historyfile, --hist TEXT  history file  [default: ~/ottopi0_cli.hist]
  -i, --host TEXT             hostname or ipaddr  [default: 0.0.0.0]
  -p, --port INTEGER          port number  [default: 8000]
  -a, --apipath TEXT          API path  [default: /api]
  -V, --version               Show the version and exit.
  -d, --debug                 debug flag
  -h, --help                  Show this message and exit.
```


**BlueToothクライアント**

``` bash
uv run ottopi0 bt -h

Usage: ottopi0 bt [OPTIONS] [BTDEV_KEYWORD]...

  JSON-RPC Client for BlueTooth controller.

Options:
  -b, --btdev TEXT    BlueTooth device keyword  [default: 8BitDo,Keyboard]
  -i, --host TEXT     hostname or ipaddr  [default: 0.0.0.0]
  -p, --port INTEGER  port number  [default: 8000]
  -a, --apipath TEXT  API path  [default: /api]
  -V, --version       Show the version and exit.
  -d, --debug         debug flag
  -h, --help          Show this message and exit.
```


**WebUIクライアント**

``` bash
uv run ottopi0 webui -h

Usage: ottopi0 webui [OPTIONS]

  WebUI Client (NiceGUI) for Robot Control.

Options:
  -i, --host TEXT           hostname or ipaddr (of jrpcsvr)  [default:
                            0.0.0.0]
  -p, --port INTEGER        port number (of jrpcsvr)  [default: 8000]
  -a, --apipath TEXT        API path (of jrpcsvr)  [default: /api]
  -w, --webui-port INTEGER  port number for WebUI  [default: 5000]
  -V, --version             Show the version and exit.
  -d, --debug               debug flag
  -h, --help                Show this message and exit.
```


**オートパイロット(自動運転)クライアント**

``` bash
uv run ottopi0 auto
```


## == サーボ制御コマンド文字列について

### === ``mv``コマンドと動作

![](docs/command-move.png)


## == 内部構造

### == Software Archives

![Software Architecture](docs/SoftwareArchitecture-20251207a.png)


### === ``mv``コマンドの内部フロー

![Servo Control Flow](docs/ServoControlFlow-20251207a.png)


## == 動画

### === 2025/12/06 途中経過

[![](docs/movie-thumbnail.png)](https://youtu.be/xyQxWBR0ToA?si=hiaeGzaGVpkgNSoV)


## == 参考

### 8BitDo Micro

Keyboard mode
![](docs/8BitDo_Micro_mode-K.jpg)

### Links
- [Otto DIY](https://www.ottodiy.com/)
