# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **CLI + MCP usage docs (MCP Phase 4)** — New `docs/cli-mcp-usage.md` with per-feature mapping of CLI commands to MCP tools (engine, portfolio, orders, strategies, backtest, analysis, indicators, optimization, safety, notifications). Documents MCP-only and CLI-only actions. Linked from README.
- **Notification system (Phase 3 Automation)** — Discord and generic webhook channels for alerts. New module `trader/notifications/` (NotificationManager, DiscordChannel, WebhookChannel, formatters). CLI: `trader notify test` and `trader notify send "message"`. Config via env (`DISCORD_WEBHOOK_URL`, `CUSTOM_WEBHOOK_URL`, `NOTIFICATIONS_ENABLED`) and optional `config/notifications.yaml` (see `config/notifications.yaml.example`). App layer: `trader/app/notifications.py` for use by engine or MCP later.
- **Central audit log (MCP Phase 3)** — `trader/audit.py` appends structured JSONL to `logs/audit.log` for sensitive actions from both CLI and MCP. Logged actions: `place_order`, `place_order_blocked`, `cancel_order`, `create_strategy`, `remove_strategy`, `run_backtest`, `stop_engine`. Each record includes timestamp (UTC), source (`cli` or `mcp`), action, details, and optional error. Audit source is set via context (CLI sets at startup; MCP sets per tool call).
- **MCP rate limits and timeouts (Phase 3)** — Long-running MCP tools (`run_backtest`, `run_optimization`) are now subject to configurable rate limits and per-call timeouts. New module `trader/mcp/limits.py`; env vars: `MCP_BACKTEST_TIMEOUT_SECONDS` (default 300), `MCP_OPTIMIZATION_TIMEOUT_SECONDS` (default 600), `MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE` (default 10). New error types: `RateLimitError`, `TaskTimeoutError` in `trader/errors.py`. See README Configuration for details.

### Fixed
- **Audit log** — Use `timezone.utc` instead of `datetime.UTC` for compatibility in all Python 3.11+ environments.

## [0.5.0] - 2026-02-11

### Documentation
- Consolidated documentation: merged DEVELOPMENT.md into CONTRIBUTING.md (single place for setup, code style, and how to make changes)
- Merged MCP-PLAN.md into PLAN.md; product phases and MCP + CLI roadmap now live in one file
- README: added Prerequisites (Python, pipx) with Mac and Windows notes; MCP section rewritten so Claude Desktop uses `"command": "trader", "args": ["mcp", "serve"]` with no wrapper script; documented config file locations for macOS and Windows; added Troubleshooting
- CONTRIBUTING: added “What is Poetry,” Mac/Windows prerequisites, MCP-for-development (pipx editable + same Claude config), dual-interface diagram, common issues, release workflow
- Replaced mcp-wrapper.sh with a stub that points users to pipx install and the README
- CLAUDE.md reference list now points to PLAN.md and CONTRIBUTING.md only

## [0.4.0] - 2026-02-10

### Added
- **MCP server with full tool parity** (`trader/mcp/`): MCP-compliant server using the official `mcp` Python SDK with stdio transport, 28 tools covering all CLI features
  - Engine: `get_status`, `stop_engine`
  - Portfolio: `get_balance`, `get_positions`, `get_portfolio`, `get_quote`
  - Orders: `place_order`, `list_orders`, `cancel_order`
  - Strategies: `list_strategies`, `get_strategy`, `create_strategy`, `remove_strategy`, `pause_strategy`, `resume_strategy`, `set_strategy_enabled`
  - Backtests: `run_backtest`, `list_backtests`, `show_backtest`, `compare_backtests`, `delete_backtest`
  - Analysis: `analyze_performance`, `get_trade_history`, `get_today_pnl`
  - Indicators: `list_indicators`, `describe_indicator`
  - Optimization: `run_optimization`
  - Safety: `get_safety_status`
  - `trader mcp serve` CLI command to launch the server
  - 27 tests for server setup, tool registration, tool responses, and CLI integration
- **Shared error hierarchy** (`trader/errors.py`): `AppError` base with typed subclasses (`ValidationError`, `NotFoundError`, `ConfigurationError`, `BrokerError`, `SafetyError`, `EngineError`) used by both CLI and MCP server
- **Pydantic v2 schema layer** (`trader/schemas/`): 11 modules defining typed contracts for all API inputs/outputs — portfolio, orders, strategies, backtests, analysis, optimization, indicators, engine status, common types, and error responses
- **Application service layer** (`trader/app/`): 10 modules providing shared business logic that both CLI and MCP server call — indicators, engine, strategies, portfolio, orders, analysis, backtests, optimization, and data/safety
- **`--json` global CLI flag**: All commands now support `--json` for structured JSON output, enabling machine-readable responses for AI agents
- **59 new tests**: Comprehensive test coverage for MCP server, errors, schemas, and app service layer

### Changed
- **CLI refactored to use app layer**: All Click commands now delegate to `trader/app/` service functions instead of directly calling domain modules. CLI is now a thin presentation adapter.
- Added `pydantic>=2.0.0` and `mcp>=1.0.0` as project dependencies

### Fixed
- **BacktestEngine indentation bug**: Fixed critical bug where `_execute_action` and helper methods were incorrectly indented inside `_align_datetime_to_index` function, causing `AttributeError` when running backtests

### Documentation
- Added `DEVELOPMENT.md` with comprehensive development guide including editable install instructions, MCP server setup, debugging tips, and common issues
- Updated README.md with correct installation instructions for development vs. production
- Updated README.md MCP server configuration with Poetry-based development example and clarifications
- Added `MCP-PLAN.md` with MCP + CLI dual-interface roadmap
- Updated MCP-PLAN.md: Phase 1 complete, switched from FastAPI to official MCP SDK

## [0.3.0] - 2026-02-07

### Added


- **Indicators library**: Built-in SMA, EMA, RSI, MACD, ATR, Bollinger Bands, OBV, and VWAP
  - `trader indicator list` and `trader indicator describe` CLI commands
  - Optional `pandas-ta` integration with pandas fallback calculations
- **Trade analysis module**: CLI and analytics for realized trade performance
  - `trader analyze` command with per-symbol stats and open-lot report
  - FIFO matching to compute win rate, profit factor, avg win/loss, and hold time
- **Strategy optimization**: Grid/random parameter search using backtests
  - `trader optimize` command with objectives and sampling
  - Optimization result persistence under `data/optimizations/`
  - Objective scoring for return, win rate, profit factor, and drawdown
- **Backtest visualization**: Interactive Bokeh charts for price/equity curves and trades
  - `trader backtest run --chart/--show` to render charts immediately
  - `trader backtest show --chart/--show` to chart existing results
  - `trader visualize` command for backtest IDs or JSON files
  - New `trader/visualization/` module with `ChartBuilder`
- **Data provider abstraction**: Pluggable historical data sources with optional Parquet caching
  - `AlpacaDataProvider` for Alpaca API historical data
  - `CSVDataProvider` for local CSV files with normalized OHLCV format
  - `CachedDataProvider` for Parquet-backed caching with TTL
  - Provider factory (`get_data_provider`) and new data config env vars
- **Backtesting system**: Complete backtesting framework for testing strategies on historical data
  - `trader backtest run` - Run backtests with CSV historical data
  - `trader backtest list` - List all saved backtest results
  - `trader backtest show` - Display detailed backtest metrics and trade history
  - `trader backtest compare` - Compare multiple backtests side-by-side
- `trader/backtest/` module with core backtesting infrastructure:
  - `HistoricalBroker` - Simulates order fills based on OHLCV bar data
  - `BacktestEngine` - Sequential bar-by-bar strategy evaluation
  - `BacktestResult` - Performance metrics (return %, win rate, profit factor, max drawdown, Sharpe ratio)
  - CSV data loading with validation
  - JSON-based result persistence
- Realistic order fill simulation:
  - Market orders fill at bar close
  - Limit orders fill at limit price if within bar range
  - Stop orders trigger when bar crosses threshold
  - Trailing stops track high watermark
- Performance metrics: total return, win rate, profit factor, max drawdown, avg win/loss, trade history
- Equity curve tracking throughout backtest
- Support for trailing-stop and bracket strategies in backtesting
- **OCO (One-Cancels-Other) bracket orders**: Full implementation with both take-profit and stop-loss
  - Sequential order placement: take-profit limit order, then stop-loss stop order
  - Automatic cancellation of remaining order when one fills
  - Proper strategy completion after OCO execution
  - Works in both live trading and backtesting environments

### Fixed

- **Total Return calculation bug**: HistoricalBroker now properly stores initial_cash for accurate metrics calculation
- **Bracket strategy phase management**: _evaluate_exiting now delegates to bracket handler for proper OCO logic

### Documentation

- Updated README.md with comprehensive backtesting section
- Added backtesting examples and best practices
- Updated feature list to reflect backtesting availability

## [0.2.0] - 2026-02-07

### Added

- `trader portfolio` command: Full portfolio overview showing account summary, positions, and open orders
- `trader orders` command: View open orders with `--all` flag for complete history
- Enhanced account data: portfolio value, day's P/L, day trade count, PDT status
- Service-based configuration with hardcoded URLs per broker (Alpaca paper/prod)

### Changed

- Simplified configuration: Separate env vars for paper (`ALPACA_API_KEY`) and prod (`ALPACA_PROD_API_KEY`)
- Replaced `--env paper/prod` with simpler `--prod` flag
- Production now uses interactive (Y/n) confirmation instead of `--confirm` flag
- `trader balance` now shows full account summary with day's change and unrealized P/L
- `trader status` now displays service name (alpaca)
- Strategy default quantity changed to 1 (was config-based)
- Strategy entry options simplified: `--limit`/`-L` replaces `--entry-type` and `--entry-price`

### Removed

- Legacy rules system (`trader rules` commands, `trader/rules/` module)
- `trader backtest` command (will be reimplemented for strategies)
- `--confirm` flag (replaced with interactive confirmation)
- `TRADER_ENV`, `BROKER`, `BASE_URL`, `ENABLE_PROD` environment variables
- Separate `.env.paper` and `.env.prod` files (now just `.env`)

## [0.1.1] - 2026-02-05

### Changed

- CLI: `rules add` default behavior refined — `sell` rules now default to trigger on price >= target (ABOVE); `buy` rules continue to default to price <= target (BELOW). Updated CLI and README examples; tests updated.

## [0.1.0] - 2026-01-29

### Added

- Project structure with Poetry package management
- CLI framework using Click with commands: status, balance, positions, rules, start, stop
- Configuration system with environment support (paper/prod)
- Logging infrastructure with file and console output
- Trade audit log capability
- Environment-based configuration (.env.paper, .env.prod)
- Safety controls: production disabled by default, confirmation flags required
- Rich terminal output with formatted tables
- Test suite with pytest

### Dependencies

- click, requests, pandas, python-dotenv, pyyaml, alpaca-py, rich
- Dev: pytest, pytest-cov, ruff, mypy

## [0.0.1] - 2026-01-30

### Added

- Initial Setup
