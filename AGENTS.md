# Repository Guidelines

## Project Structure & Module Organization
Core package code lives in `blueprints/`. Key modules:
- `blueprints/recipes/`: recipe abstractions and built-in recipe types (`base.py`, `general.py`, `static_frame.py`).
- `blueprints/factory.py`: execution engines (`Factory`, `FactoryMP`) for resolving recipe DAGs.
- `blueprints/blueprint.py`: dependency graph/build-state model.
- `blueprints/serialization.py`: JSON-friendly serialization/deserialization.
- `blueprints/renderers/`: experimental Dash-based graph rendering.
- `blueprints/tests/`: pytest suite (`test_*.py`) and fixtures (`conftest.py`).

Project config is in `pyproject.toml`; lint hooks are in `.pre-commit-config.yaml`.

## Build, Test, and Development Commands
Use uv and Python 3.11+.

```bash
uv sync --group dev                               # Create/update .venv with dev deps
uv run pytest                                     # Run test suite
uv run pytest --cov=blueprints --cov-report=term-missing
uv run ruff check .                               # Lint (includes import-order checks)
uv run ruff format .                              # Format code
uv run mypy blueprints                            # Static type checks
uv run pre-commit install                         # Enable local git hooks
```

## Coding Style & Naming Conventions
- Follow Ruff formatting/linting defaults; run `ruff format` then `ruff check`.
- Follow Pep8 conventions.

## Testing Guidelines
- Framework: `pytest`.
- Place tests in `blueprints/tests/` and name files `test_*.py`.
- Name tests by behavior (for example, `test_missing_bind`).
- Add/adjust tests for dependency ordering, missing-data behavior, and serialization when changing recipe/factory logic.

## Commit & Pull Request Guidelines
- Existing history uses short, imperative commit messages (for example, `Add prek action`, `Remove dependency`, `Disable no commit to main`).
- Prefer focused commits with clear intent; keep subject lines concise.
- Open PRs from branches (do not commit directly to `main`), include:
  - What changed and why.
  - Linked issue(s), if applicable.
  - Test evidence (`uv run pytest` output summary).
  - Screenshots only for renderer/UI-visible changes.
