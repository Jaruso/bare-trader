# 📈 AutoTrader — CLI-Based Automated Trading System

AutoTrader is a Python-based command-line trading platform designed for **rule-driven stock trading**, built with safety, testability, and long-term extensibility in mind.

It supports paper trading and live trading modes, provides a Git-style CLI interface, and is designed to evolve into a full trading platform with backtesting, APIs, and advanced strategies.

---

## 🚀 Features

* ✅ Global `trader` command
* ✅ Paper & production environments
* ✅ Rule-based auto trading
* ✅ Portfolio tracking
* ✅ Trade ledger
* ✅ Backtesting (planned)
* ✅ Safety & risk controls
* ✅ Extensible architecture

---

## 📦 Installation

### Prerequisites

* Python 3.11+
* Poetry
* Alpaca Account (Paper + Live)

---

### Install (Development)

```bash
git clone <repo-url>
cd auto-trader
poetry install
```

Run locally:

```bash
poetry run trader status
```

---

### Install (Global)

Using pipx (recommended):

```bash
# If you previously installed a different `trader` package with pipx, uninstall it first
pipx uninstall trader || true
pipx install --editable .
```

Verify:

```bash
trader status
```

If you see import errors like `ModuleNotFoundError: No module named 'trader.data'`, it's likely a different installed `trader` is being used. You can run the local code directly or install editable mode:

```bash
# Run directly from the workspace (no global install required)
python -m trader.cli.main status

# Or install the local package in editable mode
python -m pip install -e .
trader status
```

---

## ⚙️ Configuration

AutoTrader uses environment-based configuration.

### Setup Environments

Create config files:

```
.env.paper
.env.prod
```

Example `.env.paper`:

```env
TRADER_ENV=paper
BROKER=alpaca
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
BASE_URL=https://paper-api.alpaca.markets
```

Example `.env.prod`:

```env
TRADER_ENV=prod
BROKER=alpaca
ALPACA_API_KEY=your_live_key
ALPACA_SECRET_KEY=your_live_secret
BASE_URL=https://api.alpaca.markets
ENABLE_PROD=false
```

⚠️ Production trading is disabled by default.

---

## ▶️ Usage

### Check Status

```bash
trader status
```

### Start Trading Engine

Paper (default):

```bash
trader start
```

Production:

```bash
trader start --env prod --confirm
```

---

### Manage Rules

Add buy rule (trigger when price is at or below target):

```bash
trader rules add buy AAPL 170 --qty 10
```

Add sell rule (trigger when price is at or above target — this is the default for `sell`):

```bash
trader rules add sell TSLA 220 --qty 5
```

List rules:

```bash
trader rules list
```

Remove rule:

```bash
trader rules remove <id>
```

Enable / disable rule:

```bash
trader rules enable <id>
trader rules disable <id>
```

---

### View Portfolio

```bash
trader balance
trader positions
```

---

### Stop Engine

```bash
trader stop
```

---

## 🗂 Project Structure

```
auto-trader/
├── trader/         # Python package providing the `trader` CLI
│   ├── api/        # Broker integrations
│   ├── cli/        # CLI interface
│   ├── core/       # Trading engine
│   ├── rules/      # Rule system
│   ├── data/       # Storage
│   └── utils/      # Helpers
├── tests/
├── config/
├── pyproject.toml
└── README.md
```

---

## 🧪 Testing

Run all tests:

```bash
poetry run pytest
```

Linting:

```bash
poetry run ruff check .
poetry run mypy .
```

---

## 🔒 Safety & Risk Controls

AutoTrader enforces multiple layers of protection:

* Paper trading default
* Production confirmation flag
* Position size limits
* Daily loss limits
* Kill switch
* Immutable audit logs

Never deploy to production without extensive paper testing.

---

## 🗺 Roadmap

See:

* `Auto Trading CLI Tool — Agent Development Plan`

for full milestone tracking.

---

## 🤝 Contributing

Contributions are welcome.

Guidelines:

* Follow PEP8
* Write tests
* Document changes
* Keep commits atomic

---

## ⚠️ Disclaimer

This software is for educational and experimental purposes only.

It is not financial advice.

Use at your own risk.

---

## 📜 License

MIT License (Planned)
