# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
