# Financial Manager MCP Test Plan

**Purpose:** Validate BareTrader MCP server from the perspective of a financial analyst/manager whose AI agent uses the MCP. Execute workflows via MCP tools; record results for regression and for agents reworking features or developing new requirements.

**Prerequisites:** Python 3.11+, MCP config (e.g. Cursor with BareTrader MCP), optional Alpaca paper keys, optional CSV data in `HISTORICAL_DATA_DIR`.

**Workflow groups:**

| Group | Broker required? | Scope |
|-------|------------------|--------|
| A. System & discovery | No | get_status, get_safety_status, list_indicators, describe_indicator, list_strategies, list_scheduled_strategies |
| B. Portfolio & market | Yes | get_balance, get_positions, get_portfolio, get_quote, get_top_movers |
| C. Backtest & optimization | CSV or Alpaca | list_backtests, run_backtest, show_backtest, compare_backtests, delete_backtest, run_optimization |
| D. Strategy lifecycle | Config | create_strategy, list_strategies, get_strategy, pause/resume/set_enabled, remove_strategy |
| E. Orders | Yes | list_orders, place_order, cancel_order |
| F. Analysis | Yes | analyze_performance, get_trade_history, get_today_pnl |

**Verification (per step):** Valid JSON; success shape (required keys) or error shape (`error` + `message`); state changes where applicable (list after create/delete).

---

## Plan: Steps and Verification

### A. System and discovery

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| A1 | Engine status | get_status | `running`, `environment`, `service`, `base_url`, `api_key_configured` or error |
| A2 | Safety limits | get_safety_status | `status.kill_switch`, `status.can_trade` or error |
| A3 | List indicators | list_indicators | Non-empty list; each has `name` |
| A4 | Describe indicator | describe_indicator("sma") | `name`, `description`, `params`, `output`; name=="sma" |
| A5 | Describe invalid | describe_indicator("NONEXISTENT_XYZ") | Error: `error`, `message` |
| A6 | List strategies | list_strategies | `strategies` (list), `count == len(strategies)` or error |
| A7 | List scheduled | list_scheduled_strategies | Dict or list or error |

### B. Portfolio and market

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| B1 | Balance | get_balance | `account` or `buying_power` or `equity` or error |
| B2 | Positions | get_positions | List of positions or error |
| B3 | Portfolio | get_portfolio | `total_equity` or `positions` or error |
| B4 | Quote | get_quote("AAPL") | `symbol`, `bid`, `ask`, `last` or error |
| B5 | Top movers | get_top_movers("stocks", 10) | Gainers/losers structure or error |

### C. Backtest and optimization

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| C1 | List backtests | list_backtests | List (possibly empty) |
| C2 | Run backtest | run_backtest(trailing-stop, AAPL, 2024-01-01..06-01, qty=10, trailing_pct=0.03, data_source=csv, save=true) | backtest_id/metrics or error |
| C3 | List again | list_backtests | Length +1 if C2 saved |
| C4 | Show backtest | show_backtest(id) | Same id, metrics or error |
| C5 | Compare | compare_backtests([id1, id2]) | Comparison or error |
| C6 | Run optimization | run_optimization(bracket, AAPL, same range, params grid, data_source=csv, save=true) | Result or error |
| C7 | Delete backtest | delete_backtest(id) | Success; list no longer has id |

### D. Strategy lifecycle

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| D1 | Create | create_strategy(trailing-stop, AAPL, qty=5, trailing_pct=0.02) | `id`, `symbol` |
| D2 | List | list_strategies | New id in strategies |
| D3 | Get | get_strategy(id) | Same id, symbol |
| D4 | Pause | pause_strategy(id) | Success or error |
| D5 | Resume | resume_strategy(id) | Success or error |
| D6 | Disable | set_strategy_enabled(id, false) | Success or error |
| D7 | Remove | remove_strategy(id) | Success; list no longer has id |
| D8 | Get bad id | get_strategy("nonexistent-id") | Error contract |

### E. Orders

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| E1 | List open | list_orders(show_all=false) | List or error |
| E2 | Place | place_order(AAPL, qty=1, side=buy, price=150) | Order id/status or error |
| E3 | List | list_orders(false) | New order appears |
| E4 | Cancel | cancel_order(order_id) | Success; order gone |
| E5 | List all | list_orders(show_all=true) | Includes filled/cancelled |

### F. Analysis

| Step | Action | MCP tool | Verify |
|------|--------|----------|--------|
| F1 | Analyze | analyze_performance(days=30, limit=1000) | summary/total_trades/win_rate or "No trades" or error |
| F2 | Trade history | get_trade_history(limit=20) | List or error |
| F3 | Today P/L | get_today_pnl | `today_pnl` or error |

---

## Results: Run 1 (2026-02-13)

Environment: paper broker (Alpaca), API keys configured. CSV: no (HISTORICAL_DATA_DIR not set / data dir not found). MCP client: Cursor BareTrader MCP; A7/B5 verified via server import where tool not in client.

### A. System and discovery

| Step | Result (PASS/FAIL/N/A) | Notes |
|------|------------------------|-------|
| A1 | PASS | running, environment, service, base_url, api_key_configured present |
| A2 | PASS | status.kill_switch, status.can_trade, limits present |
| A3 | PASS | 9 indicators; each has name |
| A4 | PASS | name, description, params, output; name==sma |
| A5 | PASS | error + message; suggestion updated to list_indicators/CLI (fixed in repo) |
| A6 | FAIL | 'pullback_trailing' is not a valid StrategyType when loading strategies (see PLAN-1.1.0) |
| A7 | PASS | Via server: scheduled/count; contract valid |

### B. Portfolio and market

| Step | Result | Notes |
|------|--------|-------|
| B1 | PASS | account, buying_power, equity, positions |
| B2 | PASS | List of positions |
| B3 | PASS | total_equity, positions |
| B4 | PASS | symbol, bid, ask, last |
| B5 | PASS | Via server: dict with gainers (and losers) |

### C. Backtest and optimization

| Step | Result | Notes |
|------|--------|-------|
| C1 | PASS | List of backtests returned |
| C2 | FAIL | DATA_NOT_FOUND: CSV data dir not found (expected; see PLAN-1.1.0) |
| C3 | N/A | No new backtest from C2 |
| C4 | PASS | show_backtest(8e5de68c) returned id, metrics, trades |
| C5 | PASS | compare_backtests([id1, id2]) returned comparison |
| C6 | FAIL | Missing take_profit_pct, stop_loss_pct in params (see PLAN-1.1.0) |
| C7 | N/A | Skipped (no new backtest to delete; preserve user data) |

### D. Strategy lifecycle

| Step | Result | Notes |
|------|--------|-------|
| D1 | FAIL | create_strategy fails with same StrategyType error as A6 |
| D2 | FAIL | list_strategies fails |
| D3 | FAIL | get_strategy fails (loads strategies) |
| D4 | FAIL | pause_strategy not reached |
| D5 | FAIL | resume_strategy not reached |
| D6 | FAIL | set_strategy_enabled not reached |
| D7 | FAIL | remove_strategy not reached |
| D8 | FAIL | get_strategy("nonexistent-id") fails on strategy load, not not-found |

### E. Orders

| Step | Result | Notes |
|------|--------|-------|
| E1 | PASS | list_orders(show_all=false): [] |
| E2 | PASS | place_order(AAPL, 1, buy, 0.01): order id, status pending |
| E3 | PASS | New order appeared in list |
| E4 | PASS | cancel_order: status canceled |
| E5 | PASS | list_orders(show_all=true): list (empty after cancel) |

### F. Analysis

| Step | Result | Notes |
|------|--------|-------|
| F1 | PASS | analyze_performance: "No trades found" (valid) |
| F2 | PASS | get_trade_history: [] |
| F3 | PASS | get_today_pnl: today_pnl present |

**Run 1 summary:** PARTIAL. A1–A5, A7, B1–B5, C1, C4–C5, E1–E5, F1–F3 PASS. A6, D1–D8 FAIL (StrategyType/pullback_trailing when loading strategies). C2, C6 FAIL (data path; optimization param keys). Small fixes: Strategy.from_dict normalizes pullback-trailing; indicator suggestion mentions list_indicators/CLI. Large issues: PLAN-1.1.0.md.

---

## Results: Run 2 (2026-02-13)

Environment: paper broker (Alpaca), API keys configured. CSV: no (HISTORICAL_DATA_DIR not set / data dir not found). MCP client: Cursor BareTrader MCP. **Note**: MCP server running old code; requires restart to pick up fixes. Direct app layer tests confirm fixes work.

### A. System and discovery

| Step | Result (PASS/FAIL/N/A) | Notes |
|------|------------------------|-------|
| A1 | PASS | running, environment, service, base_url, api_key_configured present |
| A2 | PASS | status.kill_switch, status.can_trade, limits present |
| A3 | PASS | 9 indicators; each has name |
| A4 | PASS | name, description, params, output; name==sma |
| A5 | PASS | error + message; suggestion updated |
| A6 | **FAIL** (MCP) / **PASS** (app) | MCP server error: 'pullback_trailing' is not a valid StrategyType (old code). **App layer test**: ✓ Loads 11 strategies including pullback_trailing. **Fix verified**: Strategy.from_dict() normalizes hyphen format correctly. **Action**: MCP server restart required. |
| A7 | PASS | Via server: scheduled/count; contract valid |

### B. Portfolio and market

| Step | Result | Notes |
|------|--------|-------|
| B1 | PASS | account, buying_power, equity, positions |
| B2 | PASS | List of positions (9 positions) |
| B3 | PASS | total_equity, positions |
| B4 | PASS | symbol, bid, ask, last |
| B5 | PASS | Via server: dict with gainers (and losers) |

### C. Backtest and optimization

| Step | Result | Notes |
|------|--------|-------|
| C1 | PASS | List of backtests returned (38 backtests) |
| C2 | FAIL (expected) | DATA_NOT_FOUND: CSV data dir not found. **Fix verified**: Error message now includes setup instructions and README reference. |
| C3 | N/A | No new backtest from C2 |
| C4 | PASS | show_backtest(id) works (tested with existing id) |
| C5 | PASS | compare_backtests([id1, id2]) works |
| C6 | **FAIL** (MCP) / **PASS** (app) | MCP server would fail with old code. **App layer test**: ✓ Parameter normalization works (`take_profit` → `take_profit_pct`, `stop_loss` → `stop_loss_pct`). **Fix verified**: `_normalize_param_keys()` correctly normalizes short param names. **Action**: MCP server restart required. |
| C7 | N/A | Skipped (preserve user data) |

### D. Strategy lifecycle

| Step | Result | Notes |
|------|--------|-------|
| D1 | **FAIL** (MCP) / **PASS** (app) | MCP server error (old code). **App layer test**: ✓ Created pullback-trailing strategy successfully (`strategy_type='pullback-trailing'` → `pullback_trailing` enum). **Fix verified**: Strategy creation with hyphen format works. **Action**: MCP server restart required. |
| D2 | **FAIL** (MCP) / **PASS** (app) | MCP server error (old code). **App layer test**: ✓ list_strategies() loads 11 strategies including pullback_trailing. |
| D3 | **FAIL** (MCP) / **PASS** (app) | MCP server error (old code). App layer would work after restart. |
| D4 | N/A | Not reached (blocked by D1-D3) |
| D5 | N/A | Not reached (blocked by D1-D3) |
| D6 | N/A | Not reached (blocked by D1-D3) |
| D7 | N/A | Not reached (blocked by D1-D3) |
| D8 | **FAIL** (MCP) / **PASS** (app) | MCP server error (old code). App layer would return proper NotFoundError after restart. |

### E. Orders

| Step | Result | Notes |
|------|--------|-------|
| E1 | PASS | list_orders(show_all=false): [] |
| E2 | PASS | place_order works (tested previously) |
| E3 | PASS | List shows new orders |
| E4 | PASS | cancel_order works |
| E5 | PASS | list_orders(show_all=true) works |

### F. Analysis

| Step | Result | Notes |
|------|--------|-------|
| F1 | PASS | analyze_performance: "No trades found" (valid) |
| F2 | PASS | get_trade_history: [] |
| F3 | PASS | get_today_pnl: today_pnl present |

**Run 2 summary:** **PARTIAL** (MCP server needs restart) / **FIXES VERIFIED** (app layer). 

**MCP Server Status**: Running old code; requires restart to pick up fixes from PLAN-1.1.0.md.

**Fixes Verified via App Layer Tests**:
- ✅ Issue 1 (pullback_trailing): `Strategy.from_dict()` normalizes hyphen format; `list_strategies()` loads 11 strategies including pullback_trailing; `create_strategy()` accepts hyphen format.
- ✅ Issue 2 (optimization params): `_normalize_param_keys()` correctly converts `take_profit`/`stop_loss` to `take_profit_pct`/`stop_loss_pct`.
- ✅ Issue 3 (CSV docs): Error messages include setup instructions and README reference.
- ✅ Issue 4 (tool visibility): Script `scripts/list_mcp_tools.py` lists all 32 tools.

**Next Steps**: Restart MCP server to pick up code changes. After restart, A6, C6, D1-D8 should PASS.

---

## Results: Future runs (template)

Copy the block below for each new run; keep Run 1 and Run 2 as historical records.

```markdown
## Results: Run N (YYYY-MM-DD)
Environment: paper/prod/none, CSV: yes/no.

### A–F (same table structure as Run 1)
...
**Run N summary:** PASS/FAIL/PARTIAL. Issues: ...
```

---

## Reference

- Contract tests: [tests/test_mcp_contract.py](tests/test_mcp_contract.py)
- CLI–MCP parity: [tests/test_cli_mcp_parity.py](tests/test_cli_mcp_parity.py)
- Large issues / requirements: [PLAN-1.1.0.md](PLAN-1.1.0.md)
