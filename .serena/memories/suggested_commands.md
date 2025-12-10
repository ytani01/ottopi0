## Suggested Commands for OttoPi0 Project

### Project Setup and Installation

1.  **Install `mise` and `uv` (if not already installed):**
    ```bash
    curl https://mise.run | sh
    eval "$(~/.local/bin/mise activate bash)" # or zsh

    mise use -g uv@latest
    mise use -g python@latest
    ```

2.  **Clone repositories and build project:**
    ```bash
    for p in pi0servo pi0disp pibtinput vl53l0x_pigpio ottopi0; do git clone https://github.com/ytani01/$p; mise trust $p/mise.toml; done

    cd ottopi0
    cp ottopi0.toml.sample ~/ottopi0.toml
    mise run build
    ```

### Development Workflow

1.  **Run Tests:**
    ```bash
    uv run pytest
    ```

2.  **Run Linter (ruff):**
    ```bash
    uv run ruff check .
    # To automatically fix fixable issues:
    # uv run ruff check . --fix
    ```

3.  **Run Type Checker (mypy):**
    ```bash
    uv run mypy .
    ```

### Running the Application

1.  **Start the Server:**
    ```bash
    uv run ottopi0 svr
    ```

2.  **Run Command-Line Client:**
    ```bash
    uv run ottopi0 cmd
    ```

3.  **Run Bluetooth Client:**
    ```bash
    uv run ottopi0 bt [bt_device_keyword]
    ```

4.  **Run NiceGUI Web UI:**
    ```bash
    uv run ottopi0 webui
    ```