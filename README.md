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
