# Contributing to AutoTrader

Thanks for your interest in contributing to AutoTrader! This document covers everything you need to get started with development.

---

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: Poetry
- **CLI Framework**: Click
- **Broker**: Alpaca (paper trading first)
- **Storage**: SQLite + CSV
- **Testing**: Pytest
- **Config**: python-dotenv + YAML
- **Data**: Pandas
- **Linting**: Ruff, MyPy

---

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry
- Alpaca Account (Paper + Live)

### Clone & Install

```bash
git clone <repo-url>
cd auto-trader
poetry install
```

### Run Locally

```bash
poetry run trader status
poetry run trader --help
```

### Global Install (Development)

Using pipx for editable install:

```bash
pipx uninstall autotrader || true
pipx install --editable .
trader status
```

If you see `ModuleNotFoundError`, ensure you're using the local install and not a different `trader` package.

---

## Project Structure

```
auto-trader/
├── trader/           # Python package providing the `trader` CLI
│   ├── api/          # Broker integrations (Alpaca)
│   ├── cli/          # CLI interface (Click commands)
│   ├── core/         # Trading engine, portfolio, safety
│   ├── strategies/   # Trading strategies (trailing stop, bracket, etc.)
│   ├── data/         # Storage (ledger, SQLite)
│   ├── oms/          # Order management system
│   └── utils/        # Helpers, config, logging
├── tests/            # Pytest tests
├── config/
│   └── strategies.yaml  # Active strategies
├── pyproject.toml
├── CLAUDE.md         # AI assistant context
├── PLAN.md           # Development roadmap
└── README.md         # User documentation
```

---

## Development Commands

```bash
# Install dependencies
poetry install

# Run CLI locally
poetry run trader status
poetry run trader balance
poetry run trader strategy list

# Run tests
poetry run pytest
poetry run pytest -v              # Verbose
poetry run pytest -x              # Stop on first failure
poetry run pytest tests/test_cli.py  # Specific file

# Linting
poetry run ruff check .
poetry run ruff check . --fix     # Auto-fix

# Type checking
poetry run mypy .
```

---

## Environment Configuration

Create a `.env` file with your Alpaca credentials:

```env
# Paper trading (default)
ALPACA_API_KEY=your_paper_api_key
ALPACA_SECRET_KEY=your_paper_secret_key

# Production (optional - only needed for live trading)
ALPACA_PROD_API_KEY=your_live_api_key
ALPACA_PROD_SECRET_KEY=your_live_secret_key
```

AutoTrader defaults to paper trading. URLs are hardcoded per service:

| Service | Paper URL | Production URL |
|---------|-----------|----------------|
| alpaca | `https://paper-api.alpaca.markets` | `https://api.alpaca.markets` |

To use production, pass `--prod` flag (you'll be prompted to confirm):

```bash
trader --prod start
```

Optional strategy defaults:

```env
STRATEGY_TRAILING_STOP_PCT=5.0
STRATEGY_TAKE_PROFIT_PCT=10.0
STRATEGY_STOP_LOSS_PCT=5.0
```

---

## Development Guidelines

1. **Paper trading first** — Never touch real money until extensively tested
2. **Log everything** — All trades, errors, and state changes
3. **No silent failures** — Raise exceptions, don't swallow errors
4. **Small commits** — Atomic, focused changes
5. **Test before real money** — Integration tests with mock broker
6. **Manual override always** — User can stop/intervene at any time

---

## Safety Principles

These are non-negotiable:

- Paper trading by default
- Production requires `--prod` flag with interactive confirmation
- Separate API keys for paper vs production
- Position size limits enforced
- Daily loss limits enforced
- Kill switch available (`trader stop`)
- Immutable audit logs

---

## Code Style

- Follow PEP8
- Use type hints everywhere
- Run `ruff check .` and `mypy .` before committing
- Keep functions small and focused
- Write docstrings for public functions

---

## Testing

- Write tests for new features
- Maintain test coverage
- Use the mock broker for integration tests
- Never run tests against live APIs with real money

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=trader

# Run specific test
poetry run pytest tests/test_cli.py::test_cli_status
```

---

## Commit Guidelines

- Keep commits atomic and focused
- Use clear, descriptive commit messages
- Reference issues when applicable

Examples:
```
Add trailing-stop strategy type
Fix order status sync with Alpaca
Update CLI help text for strategy command
```

---

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run `poetry run pytest` and `poetry run ruff check .`
4. Submit PR with clear description
5. Address review feedback

---

## Roadmap

See `PLAN.md` for the full development roadmap with phases and milestones.

---

## Questions?

Open an issue for questions or discussion about contributing.
