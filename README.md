# 📈 AutoTrader — CLI-Based Automated Trading System

AutoTrader is a command-line trading platform for **automated stock trading**. It supports paper trading and live trading modes via Alpaca, with predefined trading strategies that handle complete trade lifecycles from entry to exit.

---

## 🚀 Features

* ✅ Paper & production environments
* ✅ **Trading strategies** (trailing stop, bracket, scale-out, grid)
* ✅ Portfolio tracking & trade ledger
* ✅ Safety & risk controls
* ✅ Backtesting (planned)

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
