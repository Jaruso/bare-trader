# CLI and MCP Usage by Feature

This document maps each AutoTrader feature to its **CLI commands** and **MCP tools**. Both interfaces use the same application layer (`trader/app`) and return equivalent data; use CLI for interactive use and MCP for agents (e.g. Claude Desktop).

---

## Engine

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader status` | `get_status()` | Engine state, env (paper/prod), broker, active strategy count, PID, hints |
| `trader start` [options] | — | No MCP start; engine runs as separate process |
| `trader stop` [--force] | `stop_engine(force: bool)` | Stop running engine; `force` = SIGKILL |
| `trader watch` | — | Live watch; no direct MCP equivalent |

**MCP only**: None for this group.

**CLI only**: `trader start`, `trader watch`.

---

## Portfolio & Market Data

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader portfolio` | `get_portfolio()` | Full summary: balance, positions, weights, P/L |
| `trader balance` | `get_balance()` | Account balance, equity, buying power, daily P/L |
| `trader positions` | `get_positions()` | Open positions with prices and unrealized P/L |
| `trader orders` [--all] | `list_orders(show_all: bool)` | Open orders; `--all` / `show_all` includes filled/canceled |
| `trader quote SYMBOL` | `get_quote(symbol: str)` | Bid/ask/last for symbol |

Use the **global** `--json` flag before the subcommand for JSON output comparable to MCP responses: `trader --json portfolio`, `trader --json orders`, etc.

---

## Orders

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader buy SYMBOL PRICE` [--qty] | `place_order(symbol, qty, side="buy", price)` | Limit buy |
| `trader sell SYMBOL PRICE` [--qty] | `place_order(symbol, qty, side="sell", price)` | Limit sell |
| `trader cancel ORDER_ID` | `cancel_order(order_id: str)` | Cancel open order |

Place order parameters: `symbol`, `qty` (default 1 on CLI), `side` ("buy" or "sell"), `price`. Safety checks apply to both CLI and MCP.

---

## Strategies

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader strategy list` | `list_strategies()` | All configured strategies |
| `trader strategy show STRATEGY_ID` | `get_strategy(strategy_id: str)` | Full strategy details |
| `trader strategy add TYPE SYMBOL` [options] | `create_strategy(strategy_type, symbol, qty=1, ...)` | Create strategy; see options below |
| `trader strategy remove STRATEGY_ID` | `remove_strategy(strategy_id: str)` | Delete strategy |
| `trader strategy enable STRATEGY_ID` | `set_strategy_enabled(strategy_id, enabled=True)` | Enable |
| `trader strategy disable STRATEGY_ID` | `set_strategy_enabled(strategy_id, enabled=False)` | Disable |
| `trader strategy pause STRATEGY_ID` | `pause_strategy(strategy_id: str)` | Pause |
| `trader strategy resume STRATEGY_ID` | `resume_strategy(strategy_id: str)` | Resume |
| `trader strategy explain TYPE` | — | CLI-only help for strategy type |

**create_strategy / strategy add** parameters:

- `strategy_type`: `"trailing-stop"` \| `"bracket"` \| `"scale-out"` \| `"grid"`
- `symbol`: ticker (e.g. `"AAPL"`)
- `qty`: shares (default 1)
- `trailing_pct`: for trailing-stop (CLI: `--trailing-pct`)
- `take_profit`, `stop_loss`: for bracket (CLI: `--take-profit`, `--stop-loss`)
- `entry_price`: limit entry (CLI: `--limit` / `-L`)
- `levels`: for grid (CLI: `--levels`)

---

## Backtesting

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader backtest run TYPE SYMBOL --start DATE --end DATE` [options] | `run_backtest(strategy_type, symbol, start, end, ...)` | Run backtest; rate-limited and timeout on MCP |
| `trader backtest list` [--data-dir] | `list_backtests()` | List saved backtests |
| `trader backtest show BACKTEST_ID` [options] | `show_backtest(backtest_id: str)` | Full results for one backtest |
| `trader backtest compare ID1 ID2 ...` | `compare_backtests(backtest_ids: list[str])` | Compare multiple backtests |
| — | `delete_backtest(backtest_id: str)` | **MCP only**: delete saved backtest |

**run_backtest** parameters: `strategy_type` ("trailing-stop" \| "bracket"), `symbol`, `start`, `end` (YYYY-MM-DD), `qty`, `trailing_pct` / `take_profit` / `stop_loss`, `data_source` ("csv" \| "alpaca"), `initial_capital`, `save`. MCP enforces `MCP_BACKTEST_TIMEOUT_SECONDS` and long-running rate limit.

---

## Analysis

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader analyze` [--symbol] [--days] [--limit] | `analyze_performance(symbol=None, days=30, limit=1000)` | Win rate, profit factor, etc. |
| `trader history` [--symbol] [--limit] | `get_trade_history(symbol=None, limit=20)` | Recent trade records |
| — | `get_today_pnl()` | **MCP only**: today's realized P/L |
| `trader analyze` (today view via UI) | — | CLI shows summary; use `get_today_pnl()` for raw value |

---

## Indicators

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader indicator list` | `list_indicators()` | All technical indicators (SMA, RSI, MACD, etc.) |
| `trader indicator describe NAME` | `describe_indicator(name: str)` | Details for one indicator (e.g. `"sma"`, `"rsi"`) |

---

## Optimization

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader optimize TYPE --symbol SYMBOL --start DATE --end DATE` [options] | `run_optimization(strategy_type, symbol, start, end, params, ...)` | Parameter search; rate-limited and timeout on MCP |

**run_optimization** parameters: `strategy_type`, `symbol`, `start`, `end`, `params` (e.g. `{"trailing_pct": [0.02, 0.03, 0.05]}`), `objective` ("total_return_pct", "sharpe_ratio", "win_rate", etc.), `method` ("grid" \| "random"), `num_samples` (for random), `data_source`, `initial_capital`, `save`. MCP enforces `MCP_OPTIMIZATION_TIMEOUT_SECONDS` and long-running rate limit.

---

## Safety

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader safety` | `get_safety_status()` | Position size limits, daily loss limits, trade count limits |
| `trader kill` | — | Kill switch; CLI only |

---

## Notifications

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader notify test` [--channel] | — | Test delivery (CLI only) |
| `trader notify send "MESSAGE"` [--channel] | — | Send manual message (CLI only) |

Notification MCP tools may be added in a future release.

---

## Summary: MCP-only vs CLI-only

- **MCP only**: `delete_backtest`, `get_today_pnl`.
- **CLI only**: `trader start`, `trader watch`, `trader strategy explain`, `trader kill`, `trader notify test`, `trader notify send`; backtest/visualize options like `--chart`, `--show`, `--data-dir`.

For scripted or agent use, prefer MCP tools and `trader --json <command>` for CLI when you need JSON output.

---

## Validation (manual test)

| Date       | CHANGELOG version | Scope |
|------------|-------------------|--------|
| 2026-02-11 | 0.6.0             | CLI commands and MCP parity for engine, indicators, safety, backtest list, strategy list. |

**Commands verified**: `trader --json status`, `trader --json indicator list`, `trader --json indicator describe sma`, `trader --json safety`, `trader --json backtest list`, `trader --json strategy list`. **MCP tools verified**: `get_status`, `list_indicators`, `describe_indicator("sma")`, `get_safety_status`, `list_backtests`, `list_strategies`. JSON shapes match between CLI and MCP for these endpoints.
