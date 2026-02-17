![GithubActions Badge](https://github.com/ForeverWintr/blueprints/actions/workflows/tests.yml/badge.svg)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![codecov](https://codecov.io/gh/ForeverWintr/blueprints/branch/main/graph/badge.svg?token=COLZBZZ2SR)](https://codecov.io/gh/ForeverWintr/blueprints)

Blueprints is FrameFactory 2.

Declarative Data Composition

## Getting Started (uv)

This repository uses [uv](https://docs.astral.sh/uv/) for environment and dependency management.

### Prerequisites
- Python 3.11+
- `uv` installed (for example: `brew install uv` or `pipx install uv`)

### Setup
```bash
uv sync --group dev
```
This creates/updates `.venv` and installs runtime + development dependencies.

### Common Commands
```bash
uv run pytest
uv run pytest --cov=blueprints --cov-report=xml
uv run ruff check .
uv run ruff format .
uv run mypy blueprints
uv run pre-commit install
```
