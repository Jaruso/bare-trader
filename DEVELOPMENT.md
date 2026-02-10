# AutoTrader Development Guide

## Quick Start for Local Development

### 1. Install Dependencies

```bash
# Install all dependencies including dev tools
pipx install -e .
```

This installs the package in **editable mode**, which means:
- Code changes are immediately reflected without reinstalling
- No need to run `poetry install` again after making changes
- Just use `poetry run trader <command>` and it will use your latest code

### 2. Verify Installation

```bash
# Check that the CLI works
poetry run trader status

# Run tests
poetry run pytest

# Run linter
poetry run ruff check .

# Run type checker
poetry run mypy .
```

### 3. Making Changes & Development Workflow

After making code changes:

1. **No need to reinstall** - editable mode means changes are live immediately
2. Test your changes: `poetry run trader <command>`
3. Run tests: `poetry run pytest`
4. **To test via MCP**: Open a new Claude Desktop conversation (spawns fresh server with your changes)
5. Commit your changes

**Key insight**: Each new Claude Desktop conversation spawns a new MCP server process, so your latest code is automatically picked up. No need to restart the entire app!

### 4. Setting up the MCP Server for Development

To use the MCP server with Claude Desktop in development mode:

1. Edit your Claude Desktop config:
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. Add/update the AutoTrader MCP server entry:
   ```json
   {
     "mcpServers": {
       "AutoTrader": {
         "command": "poetry",
         "args": ["run", "trader", "mcp", "serve"],
         "cwd": "/Users/YOUR_USERNAME/path/to/auto-trader",
         "env": {
           "ALPACA_API_KEY": "your_paper_key",
           "ALPACA_SECRET_KEY": "your_paper_secret"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** after updating the config

4. **To apply code changes**: Open a new Claude Desktop conversation (no full restart needed!)
   - Code changes are live immediately due to editable install
   - Each new conversation spawns a fresh MCP server process
   - Or click "Reconnect" if the server shows as disconnected

## Common Development Tasks

### Running the CLI

```bash
# Always use 'poetry run' for development
poetry run trader status
poetry run trader backtest list
poetry run trader strategy list
```

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/test_mcp_server.py

# With coverage
poetry run pytest --cov=trader

# Verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Lint
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check . --fix

# Type check
poetry run mypy .
```

### Running Backtests

```bash
# Make sure you have historical data in data/historical/
poetry run trader backtest run trailing-stop AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 10 \
  --trailing-pct 5 \
  --data-source csv
```

### Testing the MCP Server Locally

```bash
# Start the MCP server in stdio mode (for testing)
poetry run trader mcp serve

# The server will wait for MCP protocol messages on stdin
# Press Ctrl+C to stop
```

## Project Structure

```
auto-trader/
├── trader/
│   ├── api/           # Broker integrations (Alpaca)
│   ├── app/           # Application service layer (shared by CLI and MCP)
│   ├── backtest/      # Backtesting engine and historical broker
│   ├── cli/           # Click CLI commands
│   ├── core/          # Trading engine, portfolio, safety
│   ├── data/          # Data loading and caching
│   ├── indicators/    # Technical indicators library
│   ├── mcp/           # MCP server implementation
│   ├── oms/           # Order management system
│   ├── schemas/       # Pydantic models (API contracts)
│   ├── strategies/    # Trading strategies and evaluator
│   └── utils/         # Config, logging, helpers
├── tests/             # Test suite
├── data/              # Local data storage
│   ├── historical/    # CSV files for backtesting
│   ├── backtests/     # Backtest results
│   └── cache/         # Parquet cache
├── pyproject.toml     # Project metadata and dependencies
└── poetry.lock        # Locked dependency versions
```

## Dual Interface Architecture

AutoTrader uses a **dual-interface adapter pattern**:

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

- **trader/cli/**: Human-friendly interface with Rich tables
- **trader/mcp/**: Agent-friendly interface with JSON responses
- **trader/app/**: Shared service layer that both interfaces call
- **trader/schemas/**: Pydantic models for data contracts
- **trader/errors.py**: Shared error hierarchy

This means:
- Both CLI and MCP use the same business logic
- Changes in `trader/app/` benefit both interfaces
- Schemas in `trader/schemas/` ensure consistency
- Errors in `trader/errors.py` are handled uniformly

## Adding New Features

When adding a new feature:

1. **Add business logic** in `trader/app/` (e.g., `trader/app/portfolio.py`)
2. **Define schema** in `trader/schemas/` if needed (Pydantic models)
3. **Add CLI command** in `trader/cli/main.py` (uses Rich for display)
4. **Add MCP tool** in `trader/mcp/server.py` (returns JSON)
5. **Add tests** in `tests/` for both CLI and MCP
6. **Update docs** in README.md, PLAN.md, CHANGELOG.md

Example:

```python
# 1. Business logic (trader/app/portfolio.py)
def get_balance(config: Config) -> BalanceSchema:
    broker = create_broker(config)
    account = broker.get_account()
    return BalanceSchema.from_account(account)

# 2. CLI command (trader/cli/main.py)
@cli.command()
def balance():
    """Show account balance."""
    result = get_balance(config)
    # Display with Rich table
    console.print(table)

# 3. MCP tool (trader/mcp/server.py)
def get_balance() -> str:
    """Get account balance, equity, buying power, and daily P/L."""
    try:
        return _ok(get_balance(_config()))
    except AppError as e:
        return _err(e)
```

## Dependency Management

### Adding Dependencies

```bash
# Add a runtime dependency
poetry add package-name

# Add a dev dependency
poetry add --group dev package-name

# Update lock file after manual pyproject.toml edits
poetry lock

# Reinstall after lock file changes
poetry install
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific package
poetry update package-name

# Show outdated packages
poetry show --outdated
```

## Debugging Tips

### Enable Verbose Logging

Set the `LOG_LEVEL` environment variable:

```bash
LOG_LEVEL=DEBUG poetry run trader status
```

### Debug MCP Server

To see MCP protocol messages:

```bash
# Add debug logging to the server
LOG_LEVEL=DEBUG poetry run trader mcp serve
```

### Debug Backtests

Backtests log extensively. Check the logs in the output:

```bash
poetry run trader backtest run trailing-stop AAPL \
  --start 2024-01-02 \
  --end 2024-01-31 \
  --qty 10 \
  --trailing-pct 5 \
  --data-source csv 2>&1 | tee backtest.log
```

## Common Issues

### Issue: Import errors when running MCP server

**Cause**: MCP server is using an outdated installation

**Solution**:
1. Make sure Claude Desktop config uses `poetry run trader mcp serve`
2. Set the `cwd` field to your project directory
3. Restart Claude Desktop

### Issue: Changes not reflected in CLI

**Cause**: Using wrong installation method

**Solution**: Always use `poetry run trader` for development, not a global `trader` command

### Issue: Backtest errors

**Cause**: Missing historical data or incorrect data format

**Solution**:
1. Ensure CSV files exist in `data/historical/`
2. Check CSV format (columns: timestamp, open, high, low, close, volume)
3. Verify date range matches available data

### Issue: Poetry lock file out of sync

**Cause**: Manual edits to pyproject.toml

**Solution**:
```bash
poetry lock
poetry install
```

## Testing Workflow

Before committing:

```bash
# 1. Run all tests
poetry run pytest

# 2. Check code quality
poetry run ruff check .
poetry run mypy .

# 3. Test CLI commands manually
poetry run trader status
poetry run trader backtest list

# 4. If you changed MCP tools, restart Claude Desktop and test
```

## Release Workflow

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run tests: `poetry run pytest`
4. Commit changes
5. Tag release: `git tag v1.x.x`
6. Push: `git push && git push --tags`
7. Build: `poetry build`
8. Publish: `poetry publish` (requires PyPI credentials)

## Getting Help

- Check `PLAN.md` for the development roadmap
- Check `MCP-PLAN.md` for MCP-specific plans
- Check `README.md` for user documentation
- Check `CHANGELOG.md` for recent changes
- Open an issue on GitHub for bugs or feature requests
