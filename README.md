# Anvil - An Agentic Dependency Manager

<img src="https://raw.githubusercontent.com/quentesia/anvil/main/img/anvil.png" width="128">

Anvil is an AI-powered dependency upgrade system that autonomously analyzes, reasons about, and applies package updates.

## Features

✧ **Autonomous upgrade analysis** with AI-powered reasoning  
✧ **Multi-format support**: requirements.txt, poetry, uv, and conda environments  
✧ **Breaking change prediction** and mitigation strategies  
✧ **Safe rollback** on failure  
✧ **Changelog forensics** to understand what's changing

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

Check out [TODO.md](TODO.md) for a list of planned features and improvements you can help with!
Other contributions are also welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

```bash
# Run tests
pytest
```
