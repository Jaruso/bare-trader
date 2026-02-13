# PLAN 1.1.0 — Issues and requirements from Financial Manager MCP test run

Items below are **large or structural** (not fixed in Run 1). Small issues were fixed in repo (Strategy.from_dict hyphen normalizer, indicator error suggestion).

---

## 1. Strategy tools fail when config contains `pullback_trailing` (Run 1)

**Observed:** `list_strategies`, `create_strategy`, `get_strategy` (including `get_strategy("nonexistent-id")`) raise: `'pullback_trailing' is not a valid StrategyType`.

**Cause:** MCP server process may be running with an environment (e.g. different config dir or installed package) where (a) `strategies.yaml` contains a strategy with `strategy_type: pullback_trailing` or `pullback-trailing`, and (b) either the enum is not updated or YAML uses hyphen and `Strategy.from_dict` did not normalize it.

**Fixed in repo:** `Strategy.from_dict` now normalizes `"pullback-trailing"` → `"pullback_trailing"` so hyphen form in YAML loads. If the error persists, ensure the MCP server process restarts to pick up the change and that the enum `StrategyType.PULLBACK_TRAILING = "pullback_trailing"` is present in the running code.

**Follow-up:** If failures continue after restart, add acceptance of both `pullback_trailing` and `pullback-trailing` in all strategy load paths and document expected format in README/schemas.

---

## 2. `run_optimization` param keys (Run 1)

**Observed:** `run_optimization(..., params={"take_profit":[0.02,0.05],"stop_loss":[0.01,0.02]})` returns error: `Missing required parameters: take_profit_pct, stop_loss_pct`.

**Cause:** Optimization layer expects `params` keys `take_profit_pct` and `stop_loss_pct` for bracket strategy. MCP/CLI may pass `take_profit` / `stop_loss`; mapping exists for backtest but validation checks for the `_pct` keys.

**Requirement:** Document in README/MCP tool description that for bracket optimization, `params` must include `take_profit_pct` and `stop_loss_pct` (e.g. `{"take_profit_pct": [0.02, 0.05], "stop_loss_pct": [0.01, 0.02]}`). Optionally, normalize `take_profit` → `take_profit_pct` and `stop_loss` → `stop_loss_pct` in the app so both forms work.

---

## 3. Backtest/optimization data path (Run 1)

**Observed:** `run_backtest(..., data_source="csv")` returns `DATA_NOT_FOUND`: data directory not found (e.g. `/Users/joecaruso/data/historical`).

**Context:** Expected when `HISTORICAL_DATA_DIR` is not set or CSV files are missing. Not a code bug; environment/setup.

**Requirement:** Document in TEST-PLAN and README that for CSV backtests, `HISTORICAL_DATA_DIR` (or default) must exist and contain `{SYMBOL}.csv`. Consider documenting a minimal sample or default path for CI/test.

---

## 4. MCP tools not in client (Run 1)

**Observed:** `list_scheduled_strategies` and `get_top_movers` are implemented in the MCP server but may not appear in every MCP client’s tool list (e.g. Cursor).

**Action:** Run 1 verified A7 and B5 via direct server import. For full MCP-only runs, ensure client config exposes all 32+ tools or document which tools require direct invocation for testing.
