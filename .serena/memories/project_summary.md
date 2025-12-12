# OttoPi0 Project Summary

## Project Purpose
A biped robot based on "Otto DIY" that uses a Raspberry Pi Zero 2W. It's controlled via a JSON-RPC API, and can be operated with a Bluetooth controller.

## Tech Stack
- Python 3.11+
- `fastapi` for the JSON-RPC server.
- `uvicorn` to run the `fastapi` server.
- `click` for the command-line interface.
- `blessed` for terminal-based UI.
- `dynaconf` for configuration management.
- `json-rpc` for the RPC protocol.
- `hatchling` for building.
- `pi0servo` and `pibtinput` as local dependencies for servo control and Bluetooth input.
- `pytest` for testing.
- `ruff` for linting and formatting.
- `mypy`, `pyright` for static type checking.

## Codebase Structure
- `src/ottopi0`: Main application source code.
- `src/ottopi0/__main__.py`: CLI entry point.
- `src/ottopi0/rpcsvr.py`: JSON-RPC server implementation.
- `src/ottopi0/rpcclnt_bt.py`: Bluetooth RPC client implementation.
- `src/ottopi0/func_servo.py`: Servo control functions.
- `tests/`: Unit tests.
- `../pi0servo`, `../pibtinput`: Local dependencies.
