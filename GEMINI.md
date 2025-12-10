# OttoPi0 Project Analysis

## Project Overview

This project, `OttoPi0`, is a Python-based control system for a bipedal robot similar to Otto DIY, designed to run on a Raspberry Pi Zero 2W. The project follows a client-server architecture.

-   **Server**: A FastAPI web server that runs on the Raspberry Pi. It exposes a JSON-RPC 2.0 API for controlling the robot. It directly interfaces with the robot's hardware, specifically the servos, using the `pigpio` library. The server is responsible for translating high-level commands into low-level servo movements.

-   **Clients**: Several clients can connect to the JSON-RPC server to send commands:
    -   A command-line interface (`cmd`).
    -   A Bluetooth client (`bt`) for remote control with a gamepad (e.g., 8BitDo Micro).
    -   A web-based UI built with NiceGUI (`nicegui`).
    -   An autonomous mode client (`auto`) that uses a VL53L0X distance sensor.

-   **Command System**: The project uses a flexible command system where complex command sequences (like dance moves) can be defined as functions in a TOML configuration file. A command string library (`cmdstr_lib`) expands these functions into a series of primitive commands before sending them to the server.

-   **Technologies**:
    -   **Backend**: Python, FastAPI, Uvicorn, JSON-RPC.
    -   **Frontend**: NiceGUI.
    -   **Hardware Interaction**: `pigpio`, `pi0servo`, `pibtinput`, `vl53l0x-pigpio`.
    -   **CLI**: `click`.
    -   **Configuration**: `dynaconf` (using TOML files).
    -   **Project Management**: `mise`, `uv`.

## Building and Running

The project is managed using `mise` for tool versioning and `uv` for Python environment and package management.

### Installation

1.  **Install `mise` and `uv`**:
    ```bash
    # Install mise
    curl https://mise.run | sh
    eval "$(~/.local/bin/mise activate bash)" # Or zsh

    # Install uv and python
    mise use -g uv@latest
    mise use -g python@latest
    ```

2.  **Clone repositories and build**:
    ```bash
    for p in pi0servo pi0disp pibtinput vl53l0x_pigpio ottopi0; do git clone https://github.com/ytani01/$p; mise trust $p/mise.toml; done

    cd ottopi0
    cp ottopi0.toml.sample ~/ottopi0.toml
    mise run build
    ```

### Running the Server

The main robot control server is started with:

```bash
uv run ottopi0 svr
```

### Running Clients

Clients connect to the running server.

-   **Command-Line Client**:
    ```bash
    uv run ottopi0 cmd
    ```

-   **Bluetooth Client**:
    ```bash
    uv run ottopi0 bt [bt_device_keyword]
    ```

-   **NiceGUI Web UI**:
    ```bash
    uv run ottopi0 nicegui
    ```

## Development Conventions

-   **Package Management**: The project uses `uv` for managing Python dependencies. Dependencies are listed in `pyproject.toml`. Local dependencies are specified in the `[tool.uv.sources]` section.
-   **Testing**: Tests are written using `pytest`. Test files are located in the `tests/` directory. To run the tests, use:
    ```bash
    uv run pytest
    ```
-   **Linting and Type Checking**: The project uses `ruff` for linting and `mypy` for static type checking. Configuration for these tools is in `pyproject.toml`.
-   **Configuration**: Application configuration is handled by `dynaconf`. The main configuration file is `~/ottopi0.toml`, which is a copy of `ottopi0.toml.sample`. This file defines servo pins, command sequences, and client/server settings.
-   **CLI**: The command-line interface is built with `click` and is defined in `src/ottopi0/__main__.py`.
