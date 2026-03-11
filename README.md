<div align="center">

# Kodiak

### Automated trading platform for human + AI collaboration

Trade lifecycle automation with a human-first CLI and agent-first MCP interface.

![python](https://img.shields.io/badge/python-3.11%2B-blue)
![license](https://img.shields.io/badge/license-Apache%202.0-green)
![protocol](https://img.shields.io/badge/protocol-MCP-purple)
![interfaces](https://img.shields.io/badge/interfaces-CLI%20%2B%20Server-0ea5e9)

</div>

Kodiak is a **Python monorepo** with two products:
- **Kodiak CLI** (`kodiak`) — Ad-hoc calculations, predefined workloads, manual trading, and stdio MCP for local agents.
- **Kodiak Server** (`kodiak-server`) — Persistent service with REST API, streamable HTTP MCP, web UI, and scheduling for remote integrations.

Both share a common core library (`kodiak-core`). The system supports paper and live trading via Alpaca, with strategy automation that manages the full trade lifecycle from entry to exit. From 2.0.0 onward, architecture and interfaces are stable; breaking changes are rare and clearly noted in [CHANGELOG](CHANGELOG.md).

---

## Table of Contents

- [🚀 Features](#-features)
- [🤖 Using Kodiak](#-using-kodiak)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [▶️ Usage (CLI)](#️-usage-cli)
- [📊 Trading Strategies](#-trading-strategies)
- [🧪 Backtesting](#-backtesting)
- [🧪 Strategy Optimization](#-strategy-optimization)
- [📈 Indicators Library](#-indicators-library)
- [💡 Quick Start](#-quick-start)
- [🔒 Safety & Risk Controls](#-safety--risk-controls)
- [🤝 Contributing](#-contributing)
- [⚠️ Disclaimer](#️-disclaimer)

---

## 🚀 Features

Kodiak is built around a simple promise: **one trading core, two great interfaces**.

* ✅ **Human-first CLI + agent-first MCP**: run the same capabilities from terminal commands or MCP tools.
* ✅ **Strategy lifecycle automation**: define entry + exit behavior once, then let Kodiak manage the full trade lifecycle.
* ✅ **Research-to-execution workflow**: backtest, optimize, paper trade, then promote to production when validated.
* ✅ **Operational safety by default**: paper mode default, production confirmation, limits, kill switch, and audit logging.
* ✅ **Production-ready integration surface**: REST API + streamable HTTP MCP + stdio MCP for local and remote agents.

**MCP coverage:** 32 tools across engine, portfolio, orders, strategies, backtests, analysis, indicators, optimization, safety, and scheduling.

### Feature Deep Dive

- **Dual interfaces, shared business logic**  
  CLI and MCP call the same app layer and schemas, which keeps behavior consistent across humans and agents.

- **Strategy engine (entry → management → exit)**  
  Supports `trailing-stop`, `bracket`, `scale-out`, `grid`, and `pullback-trailing` strategies with stateful lifecycle phases.

- **Backtesting + optimization**  
  Validate strategy behavior on historical data (CSV/Alpaca), then run grid or random search to tune parameters.

- **Portfolio intelligence**  
  Track balances, positions, orders, and ledger history with both quick summaries and detailed inspection.

- **Risk and control plane**  
  Built-in safety controls include position and buying-power checks, daily loss protections, rate-limited long-running MCP calls, and audit trails.

- **Notifications + automation**  
  Send alerts to Discord/webhooks and run via cron (CLI) or async scheduler (server) for continuous operations.

## 🤖 Using Kodiak

**For human users**: Use the CLI. `kodiak --help` lists all commands.

**For AI agents**: Use the MCP tools (preferred). Connect via:
- CLI stdio MCP: `kodiak mcp` (for Claude Desktop, Cursor, local agents)
- Server HTTP MCP: `kodiak-server` then connect to `http://localhost:8000/mcp/` (for remote agents, Panda, Bear Claw)

CLI is for humans and testing; agents should use MCP tools for all operations.

**Quick Start**: See Installation and Configuration sections below.

## 📦 Installation

**Prerequisites**: Python 3.11+ ([python.org](https://www.python.org/downloads/)). On Windows, install from python.org and check **Add Python to PATH**.

### Option 1: CLI Only (Recommended)

For ad-hoc trading and Claude Desktop MCP:

```bash
git clone <repo-url>
cd Kodiak
pip install pipx
pipx install -e packages/cli/
```

Verify:
```bash
kodiak status
```

Config, data, and logs go to `~/.kodiak/` (macOS/Linux) or `%APPDATA%/kodiak/` (Windows).

**Configure Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "Kodiak": {
      "command": "kodiak",
      "args": ["mcp"],
      "env": {
        "ALPACA_API_KEY": "your_paper_key",
        "ALPACA_SECRET_KEY": "your_paper_secret"
      }
    }
  }
}
```

Or use the full path (run `which kodiak`):
```json
{
  "mcpServers": {
    "Kodiak": {
      "command": "/usr/local/bin/kodiak",
      "args": ["mcp"],
      "env": { ... }
    }
  }
}
```

Restart Claude Desktop after saving. Done!

### Option 2: Server + CLI (For Integration)

For Panda, Bear Claw, or remote agent integration:

```bash
git clone <repo-url>
cd Kodiak
pip install poetry
poetry install
```

Start the server:
```bash
poetry run kodiak-server
```

Server runs on `http://localhost:8000` with:
- REST API at `/api/`
- MCP endpoint at `/mcp/`
- Web UI at `/`

Remote agents connect to `http://localhost:8000/mcp/` for MCP.

CLI is also available: `poetry run kodiak status`.

### Option 3: Development

For contributing to Kodiak:

```bash
git clone <repo-url>
cd Kodiak
pip install poetry
poetry install              # Install all 3 packages
pipx install -e packages/cli/    # Optional: CLI on PATH
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

### Troubleshooting

- **"kodiak" not found**: Ensure pipx bin is on PATH. Run `pipx ensurepath`.
- **"command not found" in Claude Desktop**: Use the full path. Run `which kodiak` and use that path in the config.
- **MCP server error**: Check Alpaca API keys and JSON syntax (no trailing commas).
- **Tool not visible**: All 32 tools are registered. If a tool doesn’t appear in your client, it may be filtered. List all tools: `python3 -c "from kodiak.mcp.tools import build_server; [print(t.name) for t in build_server().list_tools()]"`

## ⚙️ Configuration

Configuration is **environment-based**: the app reads from environment variables and, when present, from a `.env` file (project root, CWD, or `~/.kodiak/.env` when installed). You can view and set values via the CLI; secrets are never shown in full when listing.

**Set API keys (persisted to `.env`):**
```bash
kodiak config set ALPACA_API_KEY your_paper_key
kodiak config set ALPACA_SECRET_KEY your_paper_secret
```

**View current config (secrets redacted):**
```bash
kodiak config list
kodiak config get ALPACA_API_KEY          # redacted
kodiak config get ALPACA_API_KEY --show-secret   # full value
kodiak config keys   # list all available keys
```

**Schedule (cron)** — CLI only:
```bash
kodiak schedule enable          # Install cron job (every 5 min default)
kodiak schedule enable --every 1  # Run every minute
kodiak schedule status          # Show whether enabled
kodiak schedule disable         # Remove cron job
```

For MCP/stdio, set keys in your `claude_desktop_config.json` `env` block so they are available to the subprocess. For CLI-only use, `kodiak config set` writes to the appropriate `.env` file.

### MCP server (optional)

When using the MCP server, you can tune rate limits and timeouts for long-running tools (`run_backtest`, `run_optimization`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_BACKTEST_TIMEOUT_SECONDS` | 300 | Max wall-clock time (seconds) for a single backtest; 0 = no limit. |
| `MCP_OPTIMIZATION_TIMEOUT_SECONDS` | 600 | Max wall-clock time (seconds) for a single optimization run; 0 = no limit. |
| `MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE` | 10 | Max number of long-running tool calls (backtest + optimization combined) per 60-second window; 0 = no limit. |

### Notifications (optional)

Alerts can be sent to Discord or a custom webhook (e.g. for trade events or manual messages):

| Variable | Description |
|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (primary channel). |
| `CUSTOM_WEBHOOK_URL` | Generic HTTP webhook URL (POST JSON with `message`). |
| `NOTIFICATIONS_ENABLED` | Set to `false` or `0` to disable all notifications. |

Optional YAML: copy `config/notifications.yaml.example` to `config/notifications.yaml` to configure events and channels. CLI: `kodiak notify test` (test delivery), `kodiak notify send "message"` (send manual message).

---

## ▶️ Usage (CLI)

### Check Status

```bash
kodiak status
```

### Start Trading Engine

```bash
kodiak start
```

For production:

```bash
kodiak --prod start
# You'll be prompted to confirm before trading with real money
```

### Stop Engine

```bash
kodiak stop
```

### Schedule (cron) mode — CLI only

Instead of running the engine as a long-lived loop, you can run one evaluation cycle on a schedule:

```bash
kodiak schedule enable          # every 5 minutes (default)
kodiak schedule enable --every 1 # every minute
kodiak schedule status          # show whether enabled and the cron line
kodiak schedule disable         # remove the cron job
```

Supported on macOS and Linux only. The job is added to your user crontab.

### View Portfolio

```bash
kodiak portfolio      # Full overview (balance + positions + orders)
kodiak balance        # Account summary with P/L
kodiak positions      # Open positions
kodiak orders         # Open orders
kodiak quote AAPL     # Get current quote
```

### Analyze Trades

```bash
# Last 30 days (default)
kodiak analyze

# Filter by symbol and time window
kodiak analyze --symbol AAPL --days 7
```

### Notifications

```bash
# Test notification delivery
kodiak notify test
kodiak notify test --channel discord

# Send a manual message
kodiak notify send "Trading paused for maintenance"
kodiak notify send "AAPL target hit" --channel discord
```

---

## 📊 Trading Strategies

Strategies are **automated trading plans** that handle both entry and exit, managing the complete trade lifecycle.

### Available Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **trailing-stop** | Rides trends, locks in gains with a trailing stop | Trending stocks you want to hold but protect gains |
| **bracket** | Take-profit AND stop-loss (first hit wins) | Trades with defined risk/reward |
| **scale-out** | Sells portions at progressive profit targets | Strong conviction plays where you want to lock some gains |
| **grid** | Buys at intervals down, sells at intervals up | Stocks that trade in a predictable range |

### Add a Strategy

```bash
# Trailing stop: buy AAPL, exit when price drops 5% from any high
kodiak strategy add trailing-stop AAPL --qty 10 --trailing-pct 5

# Bracket: buy TSLA with +10% take-profit and -5% stop-loss
kodiak strategy add bracket TSLA --qty 5 --take-profit 10 --stop-loss 5

# Scale out: buy GOOGL, sell portions at +5%, +10%, +15%
kodiak strategy add scale-out GOOGL --qty 20

# Grid: profit from NVDA's volatility with 5 buy/sell levels
kodiak strategy add grid NVDA --levels 5
```

### Strategy Options

All strategies support:

```bash
--qty INTEGER          # Number of shares (default: 1)
--limit, -L FLOAT      # Limit price for entry (default: market order)
```

Strategy-specific options:

```bash
# Trailing stop
--trailing-pct FLOAT   # Trailing stop percentage (default: 5%)

# Bracket
--take-profit FLOAT    # Take profit percentage (default: 10%)
--stop-loss FLOAT      # Stop loss percentage (default: 5%)

# Grid
--levels INTEGER       # Number of grid levels (default: 5)
```

### Manage Strategies

```bash
kodiak strategy list              # List all strategies
kodiak strategy show <id>         # Show details
kodiak strategy enable <id>       # Enable
kodiak strategy disable <id>      # Disable
kodiak strategy pause <id>        # Pause (keeps state)
kodiak strategy resume <id>       # Resume
kodiak strategy remove <id>       # Remove
kodiak strategy explain <type>    # Learn about a strategy type
```

### How Strategies Work

1. **Add a strategy** → It starts in `PENDING` phase
2. **Start the engine** → `kodiak start`
3. **Entry executes** → Strategy moves to `POSITION_OPEN`
4. **Exit conditions monitored** → Based on strategy type
5. **Exit executes** → Strategy moves to `COMPLETED`

Strategy phases: `PENDING` → `ENTRY_ACTIVE` → `POSITION_OPEN` → `EXITING` → `COMPLETED`

---

## 🧪 Backtesting

Test your trading strategies against historical data before risking real capital. Backtesting helps validate strategy logic, optimize parameters, and identify potential issues.

### Prepare Historical Data

For CSV-based backtesting, create CSV files with OHLCV data. The default directory is `data/historical/` (relative to project root) or `~/.kodiak/data/historical/` (when installed via pipx). You can override this with the `HISTORICAL_DATA_DIR` environment variable or the `--data-dir` flag.

**CSV File Format**:
- File naming: `{SYMBOL}.csv` (e.g., `AAPL.csv`, `MSFT.csv`)
- Required columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`
- Timestamp format: ISO format or `YYYY-MM-DD HH:MM:SS`

Example CSV file (`AAPL.csv`):
```csv
timestamp,open,high,low,close,volume
2024-01-02 09:30:00,185.75,186.50,185.00,185.75,50000000
2024-01-03 09:30:00,186.50,187.25,186.00,186.75,48000000
```

**Setup Steps**:
```bash
# Option 1: Use default directory (project root)
mkdir -p data/historical
# Add CSV files: data/historical/AAPL.csv, data/historical/MSFT.csv, etc.

# Option 2: Use custom directory via environment variable
export HISTORICAL_DATA_DIR=/path/to/your/data
mkdir -p $HISTORICAL_DATA_DIR
# Add CSV files: $HISTORICAL_DATA_DIR/AAPL.csv, etc.

# Option 3: Use --data-dir flag when running backtests
kodiak backtest run trailing-stop AAPL --data-dir /path/to/data ...
```

**Note**: If you get a "Data directory not found" error, check that:
1. The directory exists and contains CSV files named `{SYMBOL}.csv`
2. CSV files have the required columns (timestamp, open, high, low, close, volume)
3. The `HISTORICAL_DATA_DIR` environment variable is set correctly (if using custom path)

### Run a Backtest

```bash
# Trailing stop strategy
kodiak backtest run trailing-stop AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 10 \
  --trailing-pct 5 \
  --data-source csv \
  --data-dir data/historical

# Bracket strategy
kodiak backtest run bracket TSLA \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 5 \
  --take-profit 10 \
  --stop-loss 5 \
  --data-source csv \
  --data-dir data/historical

# Alpaca historical data (requires API keys)
kodiak backtest run trailing-stop AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 10 \
  --trailing-pct 5 \
  --data-source alpaca
```

### Options

```bash
--start YYYY-MM-DD          # Start date (required)
--end YYYY-MM-DD            # End date (required)
--qty INTEGER               # Quantity to trade (default: 10)
--initial-capital FLOAT     # Starting capital (default: 100000)
--data-source csv|alpaca|cached  # Data source
--data-dir PATH             # Directory with CSV files
--save / --no-save          # Save results (default: save)
--chart PATH                # Save chart to HTML file
--show                       # Open chart in browser
--theme dark|light           # Chart theme (default: dark)
```

Note: Parquet caching requires the optional `pyarrow` dependency
(`pip install pyarrow`).

### View Results

```bash
# List all backtests
kodiak backtest list

# Show detailed results
kodiak backtest show <backtest-id>

# Compare multiple backtests
kodiak backtest compare <id1> <id2> <id3>

# Save a chart for an existing backtest
kodiak backtest show <backtest-id> --chart charts/backtest.html

# Visualize a backtest by ID or JSON file
kodiak visualize <backtest-id> --output charts/backtest.html --historical-dir data/historical
kodiak visualize data/backtests/abc123.json --show --historical-dir data/historical
```

### What Gets Tracked

* **Performance**: Total return, return %, final equity
* **Trade Statistics**: Win rate, profit factor, total trades
* **Risk Metrics**: Max drawdown, avg win/loss, largest win/loss
* **Trade History**: Complete log of all fills with prices
* **Equity Curve**: Portfolio value over time

### Order Fill Simulation

* **Market orders**: Fill at current bar's close price
* **Limit orders**: Fill at limit price if within bar's [low, high] range
* **Stop orders**: Fill at stop price if triggered by bar's range
* **Trailing stops**: Track high watermark, trigger on pullback threshold

### Example Output

```bash
$ kodiak backtest show abc123

         Backtest Results - abc123
┌─────────────────┬────────────────────────┐
│ Symbol          │ AAPL                   │
│ Strategy        │ trailing_stop          │
│ Date Range      │ 2024-01-02 to 2024-12-31│
│ Initial Capital │ $100,000.00            │
│ Final Equity    │ $115,250.00            │
│ Total Return    │ +$15,250.00            │
│ Return %        │ +15.25%                │
│ Total Trades    │ 12                     │
│ Winning Trades  │ 8 (66.7%)              │
│ Max Drawdown    │ $3,200.00 (3.2%)       │
└─────────────────┴────────────────────────┘
```

### Best Practices

1. **Test with sufficient data**: Use at least 6-12 months of historical data
2. **Account for costs**: Results don't include slippage or commissions yet (coming in Phase 4)
3. **Validate assumptions**: Backtest results show what *could have* happened, not what *will* happen
4. **Paper trade next**: After successful backtests, validate in paper trading before going live
5. **Multiple scenarios**: Test across different market conditions (trending, ranging, volatile)

---

## 🧪 Strategy Optimization

Use `kodiak optimize` to run grid or random search over strategy parameters.

```bash
# Optimize trailing-stop percentage (grid search)
kodiak optimize trailing-stop \
  --symbol AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --params trailing_stop_pct:2,3,4 \
  --objective total_return_pct \
  --show-results

# Optimize bracket strategy with multiple parameters
kodiak optimize bracket \
  --symbol TSLA \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --params take_profit_pct:5,8 stop_loss_pct:2,4 \
  --objective profit_factor \
  --method grid \
  --show-results

# Random search with sampling
kodiak optimize trailing-stop \
  --symbol SPY \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --params trailing_stop_pct:1,2,3,4,5 \
  --method random \
  --num-samples 10 \
  --show-results
```

### Optimization Options

```bash
--params KEY:VAL1,VAL2      # Parameter grid (repeatable)
--objective total_return_pct|total_return|win_rate|profit_factor|max_drawdown_pct
--method grid|random         # Search method
--num-samples INTEGER        # Required for random search
--data-source csv|alpaca|cached
--data-dir PATH              # Historical data directory
--results-dir PATH           # Optimization results directory
--save / --no-save           # Save results (default: save)
--show-results               # Display results summary
```

Saved optimization results are stored under `data/optimizations/` by default.

---

## 📈 Indicators Library

Kodiak ships with a lightweight indicators library. If `pandas-ta` is
installed it will be used; otherwise, built-in pandas-based calculations are used.

```bash
# List indicators
kodiak indicator list

# Describe an indicator
kodiak indicator describe rsi
```

Available indicators include SMA, EMA, RSI, MACD, ATR, Bollinger Bands, OBV, VWAP,
and a rolling high/low band helper.

---

## 💡 Quick Start

```bash
# 1. Configure your Alpaca keys in .env

# 2. Check connection
kodiak status
kodiak balance

# 3. Add a strategy
kodiak strategy add trailing-stop AAPL --qty 5 --trailing-pct 5

# 4. Dry run first
kodiak start --dry-run --once

# 5. When ready, run for real
kodiak start
```

---

## 🔒 Safety & Risk Controls

Kodiak enforces multiple layers of protection:

* Paper trading by default
* Production requires `--prod` flag with interactive confirmation
* Position size limits
* Daily loss limits
* Kill switch available
* Immutable audit logs — `logs/audit.log` (JSONL) records place_order, cancel_order, create_strategy, remove_strategy, run_backtest, stop_engine from both CLI and MCP, with source and timestamp

**Never deploy to production without extensive paper testing.**

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## ⚠️ Disclaimer

This software is for educational and experimental purposes only. It is not financial advice. Use at your own risk.

---
