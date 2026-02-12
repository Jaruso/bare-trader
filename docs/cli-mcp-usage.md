# CLI and MCP Usage by Feature

This document maps each AutoTrader feature to its **CLI commands** and **MCP tools**. Both interfaces use the same application layer (`trader/app`) and return equivalent data; use CLI for interactive use and MCP for agents (e.g. Claude Desktop).

---

## Engine

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader status` | `get_status()` | Engine state, env (paper/prod), broker, active strategy count, PID, hints |
| `trader start` [options] | — | No MCP start; engine runs as separate process |
| `trader run-once` [--dry-run] | — | Run one evaluation cycle and exit; used by `trader schedule enable` |
| `trader schedule enable` [--every N] | — | Install cron job that runs `trader run-once` every N minutes (default 5) |
| `trader schedule disable` | — | Remove the AutoTrader cron job |
| `trader schedule status` | — | Show whether schedule is enabled and the cron line |
| `trader stop` [--force] | `stop_engine(force: bool)` | Stop running engine; `force` = SIGKILL |
| `trader watch` | — | Live watch; no direct MCP equivalent |

**MCP only**: None for this group.

**CLI only**: `trader start`, `trader run-once`, `trader schedule`, `trader watch`. Use `trader schedule enable` to run on a cron schedule instead of the loop.

---

## Portfolio & Market Data

| CLI | MCP Tool | Notes |
|-----|----------|--------|
| `trader portfolio` | `get_portfolio()` | Full summary: balance, positions, weights, P/L |
| `trader balance` | `get_balance()` | Account balance, equity, buying power, daily P/L |
| `trader positions` | `get_positions()` | Open positions with prices and unrealized P/L |
| `trader orders` [--all] | `list_orders(show_all: bool)` | Open orders; `--all` / `show_all` includes filled/canceled |
| `trader quote SYMBOL` | `get_quote(symbol: str)` | Bid/ask/last for symbol |
| — | `get_top_movers(market_type="stocks", limit=10)` | MCP-only: Today's top gainers and losers from Alpaca screener API |

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
| `trader strategy schedule add STRATEGY_ID SCHEDULE_AT` | `schedule_strategy(strategy_id, schedule_at: str)` | Schedule strategy to start at specific time (ISO datetime) |
| `trader strategy schedule list` | `list_scheduled_strategies()` | List all scheduled strategies |
| `trader strategy schedule cancel STRATEGY_ID` | `cancel_schedule(strategy_id: str)` | Cancel scheduled strategy |
| `trader strategy explain TYPE` | — | CLI-only help for strategy type |

**create_strategy / strategy add** parameters:

- `strategy_type`: `"trailing-stop"` \| `"bracket"` \| `"scale-out"` \| `"grid"` \| `"pullback-trailing"`
- `symbol`: ticker (e.g. `"AAPL"`)
- `qty`: shares (default 1)
- `trailing_pct`: for trailing-stop and pullback-trailing (CLI: `--trailing-pct`)
- `pullback_pct`: for pullback-trailing — buy when price drops this % from reference high (CLI: `--pullback-pct`, default 5)
- `take_profit`, `stop_loss`: for bracket (CLI: `--take-profit`, `--stop-loss`)
- `entry_price`: limit entry (CLI: `--limit` / `-L`)
- `levels`: for grid (CLI: `--levels`)

**pullback-trailing**: Waits for price to pull back X% from the observed high, then buys at market; after entry, exit is managed with a trailing stop. Holistic "buy the dip + trail" strategy.

**schedule_strategy / strategy schedule add** parameters:
- `strategy_id`: Strategy ID to schedule
- `schedule_at`: ISO datetime string (e.g., `"2026-02-13T09:30:00"`) - CLI also supports relative formats: `"+2h"`, `"tomorrow 09:30"`

Scheduled strategies are disabled until the schedule time arrives. The engine automatically enables them when the time comes.

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

## Configuration (CLI only)

Environment-based configuration (API keys, URLs, data source, etc.) is **CLI-only by design**; there are no MCP tools for setting or listing config to avoid exposing secrets over the agent interface.

| CLI | Notes |
|-----|--------|
| `trader config list` [--show-secrets] | List all known config keys and current values; secrets are redacted unless `--show-secrets` |
| `trader config get KEY` [--show-secret] | Get one value; secret redacted unless `--show-secret` |
| `trader config set KEY VALUE` | Set a value (persisted to `.env` in config directory) |
| `trader config keys` | List available config keys and descriptions (no values) |

**Behavior**: Config is read from environment variables; the app loads `.env` from project root, CWD, then config directory (e.g. `~/.autotrader/.env` when installed). Use `trader config set` to persist values. Optional overrides: `ALPACA_PAPER_BASE_URL`, `ALPACA_PROD_BASE_URL`. Secrets (API keys, webhook URLs) are never shown in full in `list` or `get` unless explicitly requested.

---

## Summary: MCP-only vs CLI-only

- **MCP only**: `delete_backtest`, `get_today_pnl`.
- **CLI only**: `trader start`, `trader watch`, `trader strategy explain`, `trader kill`, `trader notify test`, `trader notify send`, **`trader config list/set/get/keys`**; backtest/visualize options like `--chart`, `--show`, `--data-dir`.

For scripted or agent use, prefer MCP tools and `trader --json <command>` for CLI when you need JSON output.

---

## Agent Usage

AI agents using AutoTrader MCP tools should follow structured workflows for exploration, backtesting, and portfolio curation.

### Learning and Documentation

**CONTEXTS.md** - Learning and discovery log:
- **Purpose**: Raw discoveries, experiments, patterns observed during exploration
- **When to use**: Document all backtests, explorations, learnings, questions explored
- **Format**: Append-only, date-formatted entries (newest-first)
- **Content**: What agents learn during exploration and testing

**PORTFOLIO.md** - Curated strategy portfolio:
- **Purpose**: Validated, execution-ready strategies with confidence levels
- **When to use**: Only after extensive backtesting and review that meets quality thresholds
- **Format**: Structured entries with confidence levels, execution guidelines, validation history
- **Content**: Strategies that meet entry criteria (Sharpe > 1.0, win rate > 50%, 6+ months data, etc.)

**Key Distinction**: CONTEXTS.md = "What we're learning" (raw discoveries), PORTFOLIO.md = "What we're confident in" (validated strategies ready for execution).

### Available Workflows

**For Cursor** (see `.cursor/commands/`):
- `explore-mcp` - General MCP tool exploration
- `explore-backtesting` - Comprehensive backtesting exploration
- `discover-strategies` - Guided strategy discovery for non-financial users
- `curate-portfolio` - Portfolio review and curation workflow

**For Claude Desktop** (see `.claude/prompts/`):
- `explore-backtesting.md` - Comprehensive backtesting exploration
- `discover-strategies.md` - Guided strategy discovery
- `curate-portfolio.md` - Portfolio curation workflow

**Skills** (Cursor, see `.cursor/skills/`):
- `mcp-backtest-workflow.md` - Pattern for running backtests and documenting findings
- `mcp-strategy-optimization.md` - Pattern for parameter optimization
- `mcp-portfolio-review.md` - Pattern for reviewing and curating portfolio entries

### Example Workflows for Non-Financial Users

**Workflow 1: "I want to trade AAPL safely"**
1. Use `discover-strategies` prompt
2. Test all strategies on AAPL
3. Focus on risk metrics (low drawdown, high Sharpe)
4. Optimize for safety
5. Document findings in CONTEXTS.md
6. If strategy meets criteria, use `curate-portfolio` to add to PORTFOLIO.md

**Workflow 2: Comprehensive Backtesting Exploration**
1. Use `explore-backtesting` prompt
2. Test strategies across different symbols, time periods, parameters
3. Ask sophisticated questions about performance
4. Document all learnings in CONTEXTS.md
5. Identify patterns and promising strategies

**Workflow 3: Portfolio Curation**
1. Review CONTEXTS.md for strategies with multiple successful backtests
2. Validate entry criteria (Sharpe > 1.0, win rate > 50%, etc.)
3. Calculate confidence levels
4. Document execution guidelines
5. Add formatted entries to PORTFOLIO.md

### Best Practices

- Always document learnings in CONTEXTS.md (append-only, never delete)
- Only add to PORTFOLIO.md after extensive validation
- Test strategies across multiple time periods for consistency
- Use optimization tools to find optimal parameters
- Link backtest IDs for traceability
- Provide clear execution guidelines in PORTFOLIO.md entries

See [Agent Guide](agent-guide.md) for comprehensive MCP usage guide, tool reference, and detailed workflows.

---

## Validation (manual test)

| Date       | CHANGELOG version | Scope |
|------------|-------------------|--------|
| 2026-02-11 | 0.6.0             | CLI commands and MCP parity for engine, indicators, safety, backtest list, strategy list. |

**Commands verified**: `trader --json status`, `trader --json indicator list`, `trader --json indicator describe sma`, `trader --json safety`, `trader --json backtest list`, `trader --json strategy list`. **MCP tools verified**: `get_status`, `list_indicators`, `describe_indicator("sma")`, `get_safety_status`, `list_backtests`, `list_strategies`. JSON shapes match between CLI and MCP for these endpoints.
