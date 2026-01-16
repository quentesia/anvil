# Anvil

Anvil is an AI-powered dependency upgrade system that autonomously analyzes, reasons about, and applies package updates.

## Installation

To develop or use Anvil, you should install it in editable mode. We recommend using a virtual environment.

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Anvil in editable mode
pip install -e .
```

## Usage

### CLI

Once installed, you can use the `anvil` command.

> **Note**: If your project path contains spaces (e.g. `Volume 11`), the `anvil` command wrapper might fail. In that case, use the robust `python -m` method below.

```bash
# Robust method (works with spaces in paths):
python -m anvil.main check .
```

Standard method (if installed and no path issues):

```bash
anvil check .
```

### Running Tests

Anvil uses `pytest` for testing.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
```

## Testing on Other Projects

To test Anvil against one of your other project's environments:

1.  **Activate** the target project's virtual environment (e.g., `poetry shell` or `source .venv/bin/activate`).
2.  **Install** Anvil into that environment in editable mode:
    ```bash
    pip install -e "/absolute/path/to/anvil"
    ```
3.  **Run** Anvil from the target project root:
    ```bash
    anvil check .
    ```

This ensures Anvil can use `importlib.metadata` to accurately detect the versions currently installed in that specific environment.
