# 📈 AutoTrader — CLI-Based Automated Trading System

AutoTrader is a command-line trading platform for **automated stock trading**. It supports paper trading and live trading modes via Alpaca, with predefined trading strategies that handle complete trade lifecycles from entry to exit. From 1.0.0 the CLI and MCP tool set are treated as stable; breaking changes will be rare and noted in [CHANGELOG](CHANGELOG.md).

---

## 🚀 Features

* ✅ Paper & production environments
* ✅ **Trading strategies** (trailing stop, bracket, scale-out, grid)
* ✅ Portfolio tracking & trade ledger
* ✅ Safety & risk controls
* ✅ **Backtesting** with historical data
* ✅ **Notifications** (Discord webhook, generic webhook) for alerts

**Tools**: 32 MCP tools (engine, portfolio, orders, strategies, backtests, analysis, indicators, optimization, safety, scheduling). CLI commands mirror these; run `trader --help` and `trader <command> --help` for the full CLI surface.

## 🤖 MCP Server Usage

AutoTrader supports both CLI users and AI agents via an MCP-compliant server. **For AI agents**: Use the MCP server for all operations (status, strategies, backtests, etc.); the CLI is for human use. Run CLI only when testing or verifying human-facing output (e.g. `trader status` or `trader --json <cmd>`).

**Quick Start**: Install → Configure → Use. See the Installation and Configure MCP Server sections below.

### Two-Step Setup

1. **Install**: `brew install autotrader` (or `pipx install -e .`)
2. **Configure**: Add to Claude Desktop/Cursor MCP config (see below)

That's it! AutoTrader is ready to use with Claude Desktop or Cursor.

## 📦 Installation

### Installing

**[BREW NOT CURRENTLY AVAILABLE]**
To run from the CLI using an official version you can install with the `brew` package manager

Mac:
```bash
brew install autotrader
```
Public installation not currently available with Windows.

Alternatively you can install globally from the repo using pipx (recommended so `trader` is on PATH for CLI and MCP):

Mac:
```bash
sudo pipx install -e . --global
```

And verify:

```bash
trader status
```

**Note**: When installed via **pipx** or Homebrew, AutoTrader uses the same behavior: config, data, and logs go to `~/.autotrader/` (macOS) or `~/.config/autotrader/` (Linux). `trader config set` and all path resolution work identically with pipx. See the Installation section for path behavior.

### Configure MCP Server

Add AutoTrader to your Claude Desktop or Cursor MCP configuration:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "AutoTrader": {
      "command": "trader",
      "args": ["mcp", "serve"],
      "env": {
        "ALPACA_API_KEY": "your_paper_key",
        "ALPACA_SECRET_KEY": "your_paper_secret"
      }
    }
  }
}
```

**Cursor**: Add via Settings → MCP Servers with the same configuration.

**Restart** Claude Desktop or Cursor after saving the config.

#### Troubleshooting

- **"trader" command not found**: Use the full path to `trader` (run `which trader` and use that path in `command`)
- **MCP server error**: Check API keys and JSON syntax (no trailing commas)
- **Test installation**: Run `python3 scripts/test_installation.py` to verify setup
- **Tool not visible in MCP client**: All 32+ tools are registered in the server. If a tool doesn't appear in your MCP client (e.g., Cursor), it may be filtered by the client. For testing, you can import tools directly: `from trader.mcp.server import <tool_name>`. To list all registered tools, run: `python3 -c "from trader.mcp.server import mcp; [print(f'{t.name}: {t.description[:60]}...') for t in mcp.list_tools()]"`

See the Configure MCP Server and Troubleshooting sections above for setup details.

---


**Prerequisites**: Python 3.11+ ([python.org](https://www.python.org/downloads/)) and pipx ([pipx.pypa.io](https://pipx.pypa.io/)). On Windows, install Python from python.org and check **Add Python to PATH**; then run `pip install pipx` and ensure pipx’s bin directory is on PATH.

Install globally using pipx (recommended so `trader` is on PATH for CLI and MCP):

Mac:
```bash
sudo pipx install -e . --global
```

Windows:
```
//TODO
```

Verify:

```bash
trader status
```

---


## Streamable HTTP (later)

Remote URL-based MCP (`--transport streamable-http` with optional HTTPS) is implemented but not the default. We’ll document cert setup, URL format, and client config once we lock the base workflow. For now, use **stdio** (above) for all agent and Claude Desktop use.

## ⚙️ Configuration

Configuration is **environment-based**: the app reads from environment variables and, when present, from a `.env` file (project root, CWD, or `~/.autotrader/.env` when installed). You can view and set values via the CLI; secrets are never shown in full when listing.

**Set API keys (persisted to `.env`):**
```bash
trader config set ALPACA_API_KEY your_paper_key
trader config set ALPACA_SECRET_KEY your_paper_secret
```

**View current config (secrets redacted):**
```bash
trader config list
trader config get ALPACA_API_KEY          # redacted
trader config get ALPACA_API_KEY --show-secret   # full value
trader config keys   # list all available keys
```

**Schedule (cron):** Use `trader schedule enable` to install a cron job that runs one cycle on a schedule; `trader schedule disable` to remove it. See "Schedule (cron) mode" above.

For MCP/stdio, set keys in your `claude_desktop_config.json` `env` block so they are available to the subprocess. For CLI-only use, `trader config set` writes to the appropriate `.env` file.

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

Optional YAML: copy `config/notifications.yaml.example` to `config/notifications.yaml` to configure events and channels. CLI: `trader notify test` (test delivery), `trader notify send "message"` (send manual message).

---

## ▶️ Usage

### Check Status

```bash
trader status
```

### Start Trading Engine

```bash
trader start
```

For production:

```bash
trader --prod start
# You'll be prompted to confirm before trading with real money
```

### Stop Engine

```bash
trader stop
```

### Schedule (cron) mode

Instead of running the engine as a long-lived loop, you can run one evaluation cycle on a schedule. Use **`trader schedule enable`** to add a cron job that runs `trader run-once` (e.g. every 5 minutes); use **`trader schedule disable`** to remove it.

```bash
trader schedule enable          # every 5 minutes (default)
trader schedule enable --every 1 # every minute
trader schedule status          # show whether enabled and the cron line
trader schedule disable         # remove the cron job
```

Supported on macOS and Linux only. The job is added to your user crontab.

### View Portfolio

```bash
trader portfolio      # Full overview (balance + positions + orders)
trader balance        # Account summary with P/L
trader positions      # Open positions
trader orders         # Open orders
trader quote AAPL     # Get current quote
```

### Analyze Trades

```bash
# Last 30 days (default)
trader analyze

# Filter by symbol and time window
trader analyze --symbol AAPL --days 7
```

### Notifications

```bash
# Test notification delivery (requires DISCORD_WEBHOOK_URL or config)
trader notify test
trader notify test --channel discord

# Send a manual message
trader notify send "Trading paused for maintenance"
trader notify send "AAPL target hit" --channel discord
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
trader strategy add trailing-stop AAPL --qty 10 --trailing-pct 5

# Bracket: buy TSLA with +10% take-profit and -5% stop-loss
trader strategy add bracket TSLA --qty 5 --take-profit 10 --stop-loss 5

# Scale out: buy GOOGL, sell portions at +5%, +10%, +15%
trader strategy add scale-out GOOGL --qty 20

# Grid: profit from NVDA's volatility with 5 buy/sell levels
trader strategy add grid NVDA --levels 5
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
trader strategy list              # List all strategies
trader strategy show <id>         # Show details
trader strategy enable <id>       # Enable
trader strategy disable <id>      # Disable
trader strategy pause <id>        # Pause (keeps state)
trader strategy resume <id>       # Resume
trader strategy remove <id>       # Remove
trader strategy explain <type>    # Learn about a strategy type
```

### How Strategies Work

1. **Add a strategy** → It starts in `PENDING` phase
2. **Start the engine** → `trader start`
3. **Entry executes** → Strategy moves to `POSITION_OPEN`
4. **Exit conditions monitored** → Based on strategy type
5. **Exit executes** → Strategy moves to `COMPLETED`

Strategy phases: `PENDING` → `ENTRY_ACTIVE` → `POSITION_OPEN` → `EXITING` → `COMPLETED`

---

## 🧪 Backtesting

Test your trading strategies against historical data before risking real capital. Backtesting helps validate strategy logic, optimize parameters, and identify potential issues.

### Prepare Historical Data

For CSV-based backtesting, create CSV files with OHLCV data. The default directory is `data/historical/` (relative to project root) or `~/.autotrader/data/historical/` (when installed via pipx). You can override this with the `HISTORICAL_DATA_DIR` environment variable or the `--data-dir` flag.

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
trader backtest run trailing-stop AAPL --data-dir /path/to/data ...
```

**Note**: If you get a "Data directory not found" error, check that:
1. The directory exists and contains CSV files named `{SYMBOL}.csv`
2. CSV files have the required columns (timestamp, open, high, low, close, volume)
3. The `HISTORICAL_DATA_DIR` environment variable is set correctly (if using custom path)

### Run a Backtest

```bash
# Trailing stop strategy
trader backtest run trailing-stop AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 10 \
  --trailing-pct 5 \
  --data-source csv \
  --data-dir data/historical

# Bracket strategy
trader backtest run bracket TSLA \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --qty 5 \
  --take-profit 10 \
  --stop-loss 5 \
  --data-source csv \
  --data-dir data/historical

# Alpaca historical data (requires API keys)
trader backtest run trailing-stop AAPL \
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
trader backtest list

# Show detailed results
trader backtest show <backtest-id>

# Compare multiple backtests
trader backtest compare <id1> <id2> <id3>

# Save a chart for an existing backtest
trader backtest show <backtest-id> --chart charts/backtest.html

# Visualize a backtest by ID or JSON file
trader visualize <backtest-id> --output charts/backtest.html --historical-dir data/historical
trader visualize data/backtests/abc123.json --show --historical-dir data/historical
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
$ trader backtest show abc123

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

Use `trader optimize` to run grid or random search over strategy parameters.

```bash
# Optimize trailing-stop percentage (grid search)
trader optimize trailing-stop \
  --symbol AAPL \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --params trailing_stop_pct:2,3,4 \
  --objective total_return_pct \
  --show-results

# Optimize bracket strategy with multiple parameters
trader optimize bracket \
  --symbol TSLA \
  --start 2024-01-02 \
  --end 2024-12-31 \
  --params take_profit_pct:5,8 stop_loss_pct:2,4 \
  --objective profit_factor \
  --method grid \
  --show-results

# Random search with sampling
trader optimize trailing-stop \
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

AutoTrader ships with a lightweight indicators library. If `pandas-ta` is
installed it will be used; otherwise, built-in pandas-based calculations are used.

```bash
# List indicators
trader indicator list

# Describe an indicator
trader indicator describe rsi
```

Available indicators include SMA, EMA, RSI, MACD, ATR, Bollinger Bands, OBV, VWAP,
and a rolling high/low band helper.

---

## 💡 Quick Start

```bash
# 1. Configure your Alpaca keys in .env

# 2. Check connection
trader status
trader balance

# 3. Add a strategy
trader strategy add trailing-stop AAPL --qty 5 --trailing-pct 5

# 4. Dry run first
trader start --dry-run --once

# 5. When ready, run for real
trader start
```

---

## 🔒 Safety & Risk Controls

AutoTrader enforces multiple layers of protection:

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
