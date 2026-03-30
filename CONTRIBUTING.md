# Contributing to Kodiak

Thanks for your interest in contributing. This document covers setup, code style, and how to make changes.

---

## What You Need

- **Python 3.11+** — [python.org](https://www.python.org/downloads/). On Windows, install from python.org and check **Add Python to PATH**.
- **Poetry** — Dependency and project manager. It reads [pyproject.toml](pyproject.toml), locks versions in `poetry.lock`, and provides `poetry install`, `poetry run`, and `poetry add`. You still need Python installed; Poetry creates a virtual environment and installs packages. Install: [install.python-poetry.org](https://install.python-poetry.org/). On Windows, after installing ensure Poetry’s bin is on PATH.
- **pipx** (optional but recommended) — Installs the `kodiak` CLI on your PATH so you can run `kodiak` commands and use the same Claude MCP config as end users. [pipx.pypa.io](https://pipx.pypa.io/); run `pip install pipx` then `pipx ensurepath` if needed.
- **Alpaca account** — Paper (and optionally live) for testing.

---

## One-Time Setup

Kodiak is a monorepo with three Python packages: **kodiak-core** (shared library), **kodiak-cli** (CLI tool), and **kodiak-server** (REST API + MCP server). Development requires installing all three from the workspace.

```bash
git clone <repo-url>
cd Kodiak
poetry install
```

This installs all workspace packages in editable mode. To also install the `kodiak` CLI on your PATH for development:

```bash
pipx install -e packages/cli/
```

Then you can run `kodiak status` (or `poetry run kodiak status`) and use the same Claude Desktop MCP config as in the README (`command`: `kodiak`, `args`: `["mcp"]`).

---

## Running the App

**CLI**:
- With Poetry: `poetry run kodiak status`, `poetry run kodiak strategy list`, etc.
- With pipx: `kodiak status`, `kodiak strategy list`, etc.

**Server**:
- With Poetry: `poetry run kodiak-server` (starts on `http://localhost:8000`)
- Test: `curl http://localhost:8000/api/engine/status`
- The included homelab Blink deployment publishes Kodiak on `http://192.168.86.53:18000`; the container still listens on `8000` internally because host port `8000` is reserved for Portainer there.

---

## MCP for Development

**CLI MCP (stdio)**:
Use the same Claude config as in the README: set `command` to the **full path** to `kodiak` (run `which kodiak` and use that path), and `args`: `["mcp"]`, plus `env` for your Alpaca keys. Claude Desktop often uses a limited PATH and won’t find `kodiak` if you only use `"command": "kodiak"`. Install with `pipx install -e packages/cli/` so that path runs your local code. Each new Claude conversation spawns a new MCP process, so code changes are picked up without restarting Claude.

**Server MCP (streamable-http)**:
For remote agents or Panda integration, start the server: `poetry run kodiak-server` (or `kodiak-server` if installed globally). The MCP endpoint is at `http://localhost:8000/mcp/`. MCP rate limits and timeouts for long-running tools are configured via env (see README Configuration).

**Agent Development**: Use MCP tools as the primary interface for all operations. Run CLI commands only when testing or verifying human-facing output (e.g. `kodiak status` or `kodiak strategy list --json`).

**Note on tool visibility**: All 32 MCP tools are registered in `kodiak/mcp/tools.py`. Some MCP clients may filter or not display all tools. For testing, if a tool isn’t visible in your client, you can list all tools: `python3 -c "from kodiak.mcp.tools import build_server; server = build_server(); [print(f’{t.name}’) for t in server.list_tools()]"`.

---

## Project Layout

Kodiak is organized as a **monorepo with 3 packages**:

### packages/core/ — kodiak-core (shared library)

- **kodiak/app/** — Shared application services (single source of truth for business logic)
- **kodiak/mcp/tools.py** — Transport-agnostic MCP tool definitions (32 tools, `build_server()` factory, `register_tools()`)
- **kodiak/schemas/** — Pydantic v2 models (contracts)
- **kodiak/errors.py** — Shared error hierarchy
- **kodiak/core/**, **kodiak/backtest/**, **kodiak/strategies/**, **kodiak/api/**, **kodiak/data/**, **kodiak/indicators/**, **kodiak/notifications/**, **kodiak/oms/**, **kodiak/utils/** — Domain and infra

### packages/cli/ — kodiak-cli (CLI tool)

- **kodiak_cli/main.py** — Click CLI commands (human-friendly, Rich tables)
- **kodiak_cli/schedule_cron.py** — Cron scheduling for periodic runs
- Entry point: `kodiak` command

### packages/server/ — kodiak-server (REST API + MCP server)

- **kodiak_server/main.py** — FastAPI application factory
- **kodiak_server/rest/routes/** — REST API endpoints (engine, portfolio, orders, strategies)
- **kodiak_server/mcp/server.py** — Streamable-HTTP MCP transport
- **kodiak_server/scheduler/** — Async scheduler (stub)
- **kodiak_server/web/** — Web UI stub
- Entry point: `kodiak-server` command

**Dual-interface architecture**: CLI and Server both call shared `kodiak/app/` services and use `kodiak/schemas/`. One core, two adapters — no logic duplication. The app layer in `kodiak/app/` is the single source of truth for both. MCP tools are defined in `kodiak/mcp/tools.py` (transport-agnostic) and used by both `kodiak_cli` (stdio) and `kodiak_server` (HTTP).

```
┌──────────────────┐  ┌──────────────────────┐
│   kodiak-cli     │  │   kodiak-server      │
│  Click CLI       │  │  REST API (FastAPI)  │
│  stdio MCP       │  │  HTTP MCP            │
└────────┬─────────┘  └────────┬─────────────┘
         └──────────┬──────────┘
         ┌──────────┴──────────┐
         │    kodiak-core      │
         │  App services       │
         │  Pydantic schemas   │
         │  MCP tool defs      │
         │  Trading engine     │
         │  Strategies, etc.   │
         └─────────────────────┘
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
poetry run pytest                              # Run all tests
poetry run pytest -v                           # Verbose
poetry run pytest --cov=kodiak,kodiak_cli,kodiak_server  # Coverage
poetry run pytest tests/core/test_mcp_server.py          # Specific test
```

Test structure mirrors the monorepo:
- `tests/core/` — Core library tests (app services, schemas, broker, engine, etc.)
- `tests/cli/` — CLI tests
- `tests/server/` — REST API, MCP, contract, and limits tests
- `tests/integration/` — CLI–MCP parity and cross-package integration tests

Write tests for new features; use the mock broker for integration tests; never run tests against live APIs with real money.

---

## Making Changes

When adding a feature:

1. **Business logic** in `packages/core/kodiak/app/` (e.g. `portfolio.py`, `backtests.py`).
2. **Schema** in `packages/core/kodiak/schemas/` if needed (Pydantic v2 models).
3. **CLI command** in `packages/cli/kodiak_cli/main.py` (Click + Rich for display).
4. **MCP tool** in `packages/core/kodiak/mcp/tools.py` (JSON-friendly, transport-agnostic).
5. **Server REST endpoint** in `packages/server/kodiak_server/rest/routes/` if needed.
6. **Tests** in `tests/{core,cli,server,integration}/` for the affected package.
7. **Docs** — update README.md and CHANGELOG.md as needed, and use the workspace root `ROADMAP.md` for active unfinished work.

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

- **"kodiak" not found**: Pipx’s bin must be on PATH (`~/.local/bin` on Linux/macOS, `%USERPROFILE%\.local\bin` on Windows). Run `pipx ensurepath`.
- **Changes not reflected**: If you use the global `kodiak`, ensure it’s the editable install (`pipx install -e packages/cli/`). Otherwise use `poetry run kodiak`.
- **Poetry workspace issues**: Ensure you run `poetry install` from the **root** directory (where the root `pyproject.toml` with `package-mode = false` is located).
- **Import errors in tests**: Make sure tests import from the correct packages (e.g. `from kodiak_cli.main import cli` not `from kodiak.cli.main`).
- **Backtest errors**: Ensure CSV files in `data/historical/` with columns `timestamp, open, high, low, close, volume`; date range must match data.
- **Poetry lock out of sync**: After editing `pyproject.toml`, run `poetry lock` then `poetry install`.

---

## Release Workflow

Kodiak has three separate packages; version all three together:

1. Update version in `packages/core/pyproject.toml`, `packages/cli/pyproject.toml`, `packages/server/pyproject.toml`, and `CHANGELOG.md`.
2. Run `poetry run pytest` and `poetry run ruff check .` and `poetry run mypy .`.
3. Commit with message like "Release v2.1.0 (core, cli, server)", tag (`git tag v2.1.0`), push and push tags.
4. Build and publish:
   ```bash
   poetry build --directory packages/core
   poetry build --directory packages/cli
   poetry build --directory packages/server
   poetry publish
   ```
   (PyPI credentials required)

---

## Roadmap and Help

See the workspace root `ROADMAP.md` for active unfinished work. Open an issue for questions or discussion.
