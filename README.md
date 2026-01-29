# Anvil - An Agentic Dependency Manager

<img src="https://raw.githubusercontent.com/quentesia/anvil/main/img/anvil.png" width="128">

Anvil is an AI-powered dependency upgrade system that autonomously analyzes, reasons about, and applies package updates using a modular state machine workflow.

## Features

✧ **AI-powered risk assessment** with LLM-based changelog analysis
✧ **Modular workflow orchestration** using LangGraph state machines
✧ **Multi-format support**: requirements.txt, pyproject.toml, poetry, and uv
✧ **Breaking change detection** with detailed impact reports
✧ **Safe trial upgrades** with automatic rollback on test failures
✧ **Interactive TUI** for package selection and approval
✧ **Changelog forensics** from GitHub, with GitLab/Bitbucket coming soon

## Architecture

Anvil uses a **LangGraph state machine** to orchestrate the upgrade workflow through independent, testable nodes:

```
scan → select → analyze → confirm → install → test → commit/rollback
```

### Workflow Nodes

- **scan**: Discovers dependencies from project files
- **select**: Interactive TUI for package selection
- **analyze**: Fetches changelogs + AI risk assessment
- **confirm**: User approval (auto-skippable for low-risk)
- **install**: Trial installation (environment only)
- **test**: Runs project tests to verify compatibility
- **commit**: Updates manifest files on success
- **rollback**: Reverts on test failure

### Conditional Routing

The workflow adapts based on:
- **Risk level**: High-risk updates require explicit confirmation
- **Test results**: Automatic rollback on failures
- **User decisions**: Skip or proceed with individual packages

This architecture enables:
- Independent testing of each node
- Easy extension with custom nodes
- Foundation for parallel processing
- Clear separation of concerns

## Installation

**Recommended**: Install via `pipx` for isolation.

```bash
pipx install anvil-py
```

Or with `pip` (not recommended as it may conflict with project dependencies):

```bash
pip install anvil-py
```

## Configuration

Anvil requires an LLM to perform AI analysis. You have two options:

### Option 1: Local Ollama (Free)

Install and run [Ollama](https://ollama.ai) locally:

```bash
# Install Ollama, then pull a model
ollama pull llama3.2
```

Anvil will automatically use Ollama if it's running on `localhost:11434`.

### Option 2: OpenAI API

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Anvil will use OpenAI's models for analysis when the API key is present.

## Quick Start

Go to your project directory (supports `pip`, `poetry`, or `uv`) and run:

```bash
anvil upgrade
```

Anvil will:

1.  Detect your dependencies.
2.  Check for updates.
3.  Fetch changelogs & perform **AI Forensic Analysis**.
4.  Safely **Trial Install**, **Test**, and **Commit** upgrades.

## Usage

### Interactive Upgrade (Recommended)

The main way to use Anvil is the interactive wizard:

```bash
anvil upgrade
```

### Analysis Only (Dry Run)

If you just want to see what packages are outdated and read their changelogs without making changes:

```bash
anvil check .
```

### Check Version

```bash
anvil version
```

## Development

If you want to contribute to Anvil:

### Setup

```bash
# Clone the repository
git clone https://github.com/quentesia/anvil.git
cd anvil

# Install in development mode
pip install -e .

# Install dev dependencies
pip install pytest ruff mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anvil tests/

# Run specific test file
pytest tests/test_graph_nodes.py -v
```

### Architecture Overview

The codebase is organized as follows:

```
src/anvil/
├── agent/              # AI and workflow orchestration
│   ├── brain.py        # RiskAssessor (AI analysis)
│   ├── graph.py        # LangGraph state machine
│   ├── state.py        # State definitions
│   └── nodes/          # Workflow nodes
├── core/               # Core logic
│   ├── upgrader.py     # Main orchestrator
│   ├── scanner.py      # Codebase analysis
│   └── models.py       # Data models
├── retrievers/         # Changelog retrieval
│   ├── github.py       # GitHub API
│   └── pypi.py         # PyPI metadata
├── tools/              # External commands
│   ├── package.py      # Package manager wrapper
│   └── runner.py       # Test runner
└── ui/                 # User interface
    └── dashboard.py    # TUI dashboard
```

### Adding a Custom Node

To add a new node to the workflow:

1. Create a new file in `src/anvil/agent/nodes/your_node.py`
2. Implement the node function:
   ```python
   def your_node(state: UpgradeWorkflowState) -> dict:
       # Your logic here
       return {"phase": "next_phase", ...}
   ```
3. Register it in `src/anvil/agent/graph.py`
4. Add tests in `tests/test_graph_nodes.py`

Check out [TODO.md](TODO.md) for a list of planned features and improvements you can help with!

For major changes, please open an issue first to discuss what you would like to change.
