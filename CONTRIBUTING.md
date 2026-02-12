# Contributing to AutoTrader

Thanks for your interest in contributing. This document covers setup, code style, and how to make changes.

---

## What You Need

- **Python 3.11+** — [python.org](https://www.python.org/downloads/). On Windows, install from python.org and check **Add Python to PATH**.
- **Poetry** — Dependency and project manager. It reads [pyproject.toml](pyproject.toml), locks versions in `poetry.lock`, and provides `poetry install`, `poetry run`, and `poetry add`. You still need Python installed; Poetry creates a virtual environment and installs packages. Install: [install.python-poetry.org](https://install.python-poetry.org/). On Windows, after installing ensure Poetry’s bin is on PATH.
- **pipx** (optional but recommended) — Puts the `trader` CLI on your PATH so you can run `trader` and use the same Claude MCP config as end users. [pipx.pypa.io](https://pipx.pypa.io/); run `pip install pipx` then `pipx ensurepath` if needed.
- **Alpaca account** — Paper (and optionally live) for testing.

---

## One-Time Setup

```bash
git clone <repo-url>
cd auto-trader
poetry install
```

Optional: install the CLI on your PATH for development so `trader` uses your local code:

```bash
pipx install -e .
```

Then you can run `trader status` (or `poetry run trader status`) and use the same Claude Desktop MCP config as in the README (`command`: `trader`, `args`: `["mcp", "serve"]`).

---

## Running the App

- With Poetry only: `poetry run trader status`, `poetry run trader backtest list`, etc.
- With pipx editable install: `trader status`, `trader backtest list`, etc.

---

## MCP for Development

Use the same Claude config as in the README: set `command` to the **full path** to `trader` (run `which trader` and use that path), and `args`: `["mcp", "serve"]`, plus `env` for your Alpaca keys. Claude Desktop often uses a limited PATH and won’t find `trader` if you only use `"command": "trader"`. Install with `pipx install -e .` from the repo root so that path runs your local code. Each new Claude conversation spawns a new MCP process, so code changes are picked up without restarting Claude. MCP rate limits and timeouts for long-running tools are configured via env (see README Configuration).

---

## Project Layout

- **trader/app/** — Shared application services (single source of truth for business logic)
- **trader/cli/** — Click CLI (human-friendly, Rich tables)
- **trader/mcp/** — MCP server (agent-friendly, JSON)
- **trader/schemas/** — Pydantic models (contracts)
- **trader/errors.py** — Shared error hierarchy
- **trader/core/**, **trader/backtest/**, **trader/strategies/**, **trader/api/**, **trader/data/**, **trader/indicators/**, **trader/oms/**, **trader/utils/** — Domain and infra

**Dual-interface architecture**: CLI and MCP are thin adapters; both call `trader/app` and use `trader/schemas`. One core, two adapters — no logic duplication.

```
┌─────────────┐      ┌─────────────┐
│   CLI       │      │  MCP Server │
│  (Click)    │      │  (FastMCP)  │
└──────┬──────┘      └──────┬──────┘
       │                    │
       └────────┬───────────┘
                │
         ┌──────▼──────┐
         │  trader/app │  ← Shared business logic
         │  (Services) │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│ core/  │ │ backtest│ │  api/  │
│strategies│ │ data/  │ │ oms/   │
└────────┘ └────────┘ └────────┘
```

---

## Code Style

- Follow PEP 8; use type hints; keep functions small; docstrings for public functions.
- Run before committing:

```bash
poetry run ruff check .
poetry run ruff check . --fix   # auto-fix
poetry run mypy .
```

---

## Tests

```bash
poetry run pytest
poetry run pytest -v
poetry run pytest --cov=trader
poetry run pytest tests/test_mcp_server.py
```

Write tests for new features; use the mock broker for integration tests; never run tests against live APIs with real money.

---

## Making Changes

When adding a feature:

1. **Business logic** in `trader/app/` (e.g. `portfolio.py`, `backtests.py`).
2. **Schema** in `trader/schemas/` if needed (Pydantic models).
3. **CLI** in `trader/cli/main.py` (Rich for display).
4. **MCP tool** in `trader/mcp/server.py` (JSON).
5. **Tests** in `tests/` for CLI and/or MCP.
6. **Docs** — update README.md, CHANGELOG.md, and PLAN.md as needed.

For product and safety overview, see [README.md](README.md).

---

## Dependencies

```bash
poetry add package-name              # runtime
poetry add --group dev package-name  # dev
poetry lock                          # after manual pyproject.toml edits
poetry install
poetry update                        # update all
poetry show --outdated
```

---

## Common Issues

- **"trader" not found**: Pipx’s bin must be on PATH (`~/.local/bin` on Linux/macOS, `%USERPROFILE%\.local\bin` on Windows). Run `pipx ensurepath`.
- **Changes not reflected**: If you use the global `trader`, ensure it’s the editable install (`pipx install -e .`). Otherwise use `poetry run trader`.
- **Backtest errors**: Ensure CSV files in `data/historical/` with columns `timestamp, open, high, low, close, volume`; date range must match data.
- **Poetry lock out of sync**: After editing `pyproject.toml`, run `poetry lock` then `poetry install`.

---

## Release Workflow

1. Update version in `pyproject.toml` and `CHANGELOG.md`.
2. Run `poetry run pytest` and `poetry run ruff check .` and `poetry run mypy .`.
3. Commit, tag (`git tag v1.x.x`), push and push tags.
4. `poetry build` then `poetry publish` (PyPI credentials required).

---

## Roadmap and Help

See [PLAN.md](PLAN.md) for the development roadmap. Open an issue for questions or discussion.
