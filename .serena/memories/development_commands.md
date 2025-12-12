# OttoPi0 Development Commands

## Running the Application
- **Run the RPC server:**
  ```bash
  ottopi0 rpcsvr
  ```
- **Run the Bluetooth client:**
  ```bash
  ottopi0 rpcclntbt <btdev_keyword>
  ```

## Development Tasks
- **Testing:**
  ```bash
  pytest
  ```
- **Linting:**
  ```bash
  ruff check .
  ```
- **Formatting:**
  ```bash
  ruff format .
  ```
- **Type Checking:**
  ```bash
  mypy .
  ```
  or
  ```bash
  pyright .
  ```
