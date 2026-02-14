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
Use Poetry and Python 3.11+.

```bash
poetry install --with dev      # Install runtime + dev dependencies
poetry run pytest              # Run test suite
poetry run pytest --cov=blueprints --cov-report=term-missing
poetry run ruff check .        # Lint (includes import-order checks)
poetry run ruff format .       # Format code
poetry run mypy blueprints     # Static type checks
poetry run pre-commit install  # Enable local git hooks
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
  - Test evidence (`poetry run pytest` output summary).
  - Screenshots only for renderer/UI-visible changes.
