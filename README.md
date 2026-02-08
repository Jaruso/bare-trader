# 📈 AutoTrader — CLI-Based Automated Trading System

AutoTrader is a command-line trading platform for **automated stock trading**. It supports paper trading and live trading modes via Alpaca, with predefined trading strategies that handle complete trade lifecycles from entry to exit.

---

## 🚀 Features

* ✅ Paper & production environments
* ✅ **Trading strategies** (trailing stop, bracket, scale-out, grid)
* ✅ Portfolio tracking & trade ledger
* ✅ Safety & risk controls
* ✅ **Backtesting** with historical data

---

## 📦 Installation

Install globally using pipx:

```bash
pipx install autotrader
```

Verify:

```bash
trader status
```

---

## ⚙️ Configuration

Create a `.env` file with your Alpaca credentials:

```env
# Paper trading (default)
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret

# Production (optional - only needed for live trading)
ALPACA_PROD_API_KEY=your_live_key
ALPACA_PROD_SECRET_KEY=your_live_secret
```

AutoTrader defaults to paper trading.

Optional data settings:

```env
# Data source: csv, alpaca, cached
DATA_SOURCE=csv

# CSV data location (used for csv/cached sources)
HISTORICAL_DATA_DIR=data/historical

# Cache settings (Parquet)
DATA_CACHE_ENABLED=true
DATA_CACHE_BACKEND=parquet
DATA_CACHE_DIR=data/cache
DATA_CACHE_TTL_MINUTES=60

# Alpaca data feed override (optional)
ALPACA_DATA_FEED=
```

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

### View Portfolio

```bash
trader portfolio      # Full overview (balance + positions + orders)
trader balance        # Account summary with P/L
trader positions      # Open positions
trader orders         # Open orders
trader quote AAPL     # Get current quote
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

Create CSV files in `data/historical/` with OHLCV data (for `csv` data source):

```csv
timestamp,open,high,low,close,volume
2024-01-02 09:30:00,185.75,186.50,185.00,185.75,50000000
2024-01-03 09:30:00,186.50,187.25,186.00,186.75,48000000
```

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
* Immutable audit logs

**Never deploy to production without extensive paper testing.**

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## ⚠️ Disclaimer

This software is for educational and experimental purposes only. It is not financial advice. Use at your own risk.

---
