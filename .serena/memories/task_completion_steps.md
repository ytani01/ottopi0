After completing a task or making code changes, follow these steps to ensure code quality and functionality:

1.  **Run Tests**: Execute the project's tests to verify that changes haven't introduced regressions and new features work as expected.
    ```bash
    uv run pytest
    ```

2.  **Run Linter**: Check for style violations and potential errors using `ruff`.
    ```bash
    uv run ruff check .
    # To automatically fix fixable issues:
    # uv run ruff check . --fix
    ```

3.  **Run Type Checker**: Ensure type consistency and catch type-related bugs using `mypy`.
    ```bash
    uv run mypy .
    ```

Ensure all these commands pass without errors or warnings before considering the task complete.