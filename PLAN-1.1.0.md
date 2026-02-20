# PLAN 1.1.0 — Issues and Requirements from Financial Manager MCP Test Run

**Source**: TEST-PLAN.md Run 1 (2026-02-13)  
**Scope**: Large or structural issues (not fixed in Run 1). Small fixes already committed: `Strategy.from_dict` hyphen normalizer, indicator error suggestion.

---

## Issue 1: Strategy Tools Fail When Config Contains `pullback_trailing` 🔴

**Status**: 🔴 **OPEN** — Partial fix committed; requires verification and potential follow-up

**Priority**: ⭐⭐⭐⭐⭐ (Blocks all strategy operations)

### Why This Matters
- **For Humans**: Cannot list, create, or manage strategies if config contains `pullback_trailing` type
- **For AI Agents**: Strategy lifecycle operations (`list_strategies`, `create_strategy`, `get_strategy`) fail with `StrategyType` validation error
- **For MCP Server**: Breaks core workflow for financial manager persona

### Observed Behavior
- `list_strategies()` raises: `'pullback_trailing' is not a valid StrategyType`
- `create_strategy()` fails with same error (when loading existing strategies)
- `get_strategy(strategy_id)` fails (even for non-existent IDs, because it loads all strategies first)
- Error occurs when `strategies.yaml` contains `strategy_type: pullback_trailing` or `pullback-trailing`

### Root Cause Analysis
1. **YAML format mismatch**: Config may store `strategy_type: pullback-trailing` (hyphen) but enum expects `pullback_trailing` (underscore)
2. **Enum loading**: `Strategy.from_dict()` calls `StrategyType(data["strategy_type"])` which fails if value doesn't match enum exactly
3. **MCP process environment**: MCP server may run with different config dir or installed package version than development environment

### Implementation Details

#### Files to Modify
- ✅ `trader/strategies/models.py` — **FIXED**: Added normalization `"pullback-trailing"` → `"pullback_trailing"` in `Strategy.from_dict()`
- 🔄 `trader/app/strategies.py` — Verify all strategy load paths normalize hyphen form
- 🔄 `trader/strategies/loader.py` — Ensure `load_strategies()` uses normalized `from_dict()`
- 📝 `README.md` / `CONTRIBUTING.md` — Document expected `strategy_type` format in YAML

#### Code Changes Required

**Already Fixed** (`trader/strategies/models.py`):
```python
@classmethod
def from_dict(cls, data: dict) -> "Strategy":
    """Create strategy from dictionary."""
    raw = data["strategy_type"]
    # Normalize CLI-style hyphen to enum value (e.g. pullback-trailing -> pullback_trailing)
    if raw == "pullback-trailing":
        raw = "pullback_trailing"
    return cls(
        ...
        strategy_type=StrategyType(raw),
        ...
    )
```

**Follow-up Actions** (if error persists after MCP restart):
1. Verify enum `StrategyType.PULLBACK_TRAILING = "pullback_trailing"` exists in running code
2. Add normalization for `pullback_trailing` → `pullback_trailing` (idempotent)
3. Audit all strategy load paths (`load_strategies`, `get_strategy`, `create_strategy` validation)
4. Add test: `test_strategy_load_with_hyphen_format()` in `tests/test_strategies.py`

### Acceptance Criteria
- ✅ `Strategy.from_dict()` normalizes `"pullback-trailing"` → `"pullback_trailing"`
- 🔄 `list_strategies()` succeeds when config contains hyphen or underscore form
- 🔄 `create_strategy()` succeeds regardless of existing config format
- 🔄 `get_strategy()` succeeds (including non-existent IDs returning proper NotFoundError)
- 🔄 MCP server restart picks up code changes
- 📝 Documentation updated with expected YAML format

### Testing Strategy
```python
# tests/test_strategies_loader.py
def test_load_strategy_with_hyphen_format():
    """Test that strategies.yaml with pullback-trailing loads correctly."""
    data = {"strategy_type": "pullback-trailing", ...}
    strategy = Strategy.from_dict(data)
    assert strategy.strategy_type == StrategyType.PULLBACK_TRAILING

def test_list_strategies_with_mixed_formats():
    """Test list_strategies when config has both hyphen and underscore forms."""
    # Create test config with both formats
    # Verify list_strategies() succeeds
```

---

## Issue 2: `run_optimization` Parameter Key Mismatch 🔴

**Status**: 🔴 **OPEN** — Documentation/validation gap

**Priority**: ⭐⭐⭐⭐ (Blocks optimization workflow)

### Why This Matters
- **For Humans**: Optimization fails with confusing error about missing params
- **For AI Agents**: Cannot optimize bracket strategies via MCP without knowing internal param key format
- **For MCP Server**: Tool contract doesn't match actual validation requirements

### Observed Behavior
- `run_optimization(strategy_type="bracket", ..., params={"take_profit": [0.02, 0.05], "stop_loss": [0.01, 0.02]})` returns: `Missing required parameters: take_profit_pct, stop_loss_pct`
- MCP tool description doesn't specify required param key format
- Backtest accepts `take_profit` / `stop_loss` but optimization requires `take_profit_pct` / `stop_loss_pct`

### Root Cause Analysis
1. **Inconsistent naming**: Backtest layer accepts `take_profit` / `stop_loss`; optimization layer expects `take_profit_pct` / `stop_loss_pct`
2. **Validation mismatch**: `_validate_optimization_params()` checks for `_pct` keys directly
3. **Missing normalization**: No mapping layer converts CLI/MCP-friendly names to internal format

### Implementation Details

#### Files to Modify
- 🔄 `trader/app/optimization.py` — Add normalization for `take_profit` → `take_profit_pct`, `stop_loss` → `stop_loss_pct` in `_validate_optimization_params()` or before validation
- 📝 `trader/mcp/server.py` — Update `run_optimization` docstring to specify required param keys
- 📝 `README.md` — Document optimization param format in MCP/CLI sections
- 🔄 `trader/schemas/optimization.py` — Consider adding Pydantic validator to normalize keys

#### Code Changes Required

**Option A: Normalize in app layer** (`trader/app/optimization.py`):
```python
def _normalize_param_keys(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize CLI/MCP-friendly param names to internal format."""
    normalized = params.copy()
    if "take_profit" in normalized and "take_profit_pct" not in normalized:
        normalized["take_profit_pct"] = normalized.pop("take_profit")
    if "stop_loss" in normalized and "stop_loss_pct" not in normalized:
        normalized["stop_loss_pct"] = normalized.pop("stop_loss")
    return normalized

def run_optimization(config: Config, request: OptimizeRequest) -> OptimizeResponse:
    """Run strategy parameter optimization."""
    # Normalize param keys before validation
    request.params = _normalize_param_keys(request.params)
    _validate_optimization_params(request.strategy_type, request.params)
    ...
```

**Option B: Document only** (if normalization is undesirable):
- Update MCP tool docstring: `params` must use `take_profit_pct` and `stop_loss_pct` for bracket strategy
- Update README with example: `{"take_profit_pct": [0.02, 0.05], "stop_loss_pct": [0.01, 0.02]}`

### Acceptance Criteria
- 🔄 `run_optimization(..., params={"take_profit": [...], "stop_loss": [...]})` succeeds (if Option A)
- 📝 MCP tool docstring clearly states required param key format
- 📝 README includes optimization param examples
- 🔄 Test: `test_optimization_with_short_param_names()` verifies normalization

### Testing Strategy
```python
# tests/test_optimization.py
def test_optimization_normalizes_param_keys():
    """Test that take_profit/stop_loss normalize to _pct form."""
    request = OptimizeRequest(
        strategy_type="bracket",
        params={"take_profit": [0.02], "stop_loss": [0.01]},
        ...
    )
    # Verify normalization happens before validation
    result = run_optimization(config, request)
    assert result is not None
```

---

## Issue 3: Backtest/Optimization CSV Data Path Documentation 🔴

**Status**: 🔴 **OPEN** — Documentation gap

**Priority**: ⭐⭐⭐ (User experience)

### Why This Matters
- **For Humans**: Unclear how to set up CSV data for backtesting
- **For AI Agents**: Cannot run CSV backtests without knowing expected directory structure
- **For MCP Server**: Error message helpful but setup not documented

### Observed Behavior
- `run_backtest(..., data_source="csv")` returns: `DATA_NOT_FOUND: Data directory not found: /Users/joecaruso/data/historical`
- Error message suggests path but doesn't explain how to configure it
- No documentation on CSV file format or directory structure

### Root Cause Analysis
1. **Environment variable**: `HISTORICAL_DATA_DIR` not set; defaults to `~/data/historical` or config dir
2. **Missing docs**: README doesn't explain CSV setup for backtesting
3. **No examples**: No sample CSV files or directory structure documented

### Implementation Details

#### Files to Modify
- 📝 `README.md` — Add "Backtesting with CSV Data" section
- 📝 `CONTRIBUTING.md` — Document CSV format and test data setup
- 📝 `trader/backtest/data.py` — Improve error message with setup instructions
- 🔄 `config/` — Consider adding `backtest.yaml.example` with CSV path example

#### Documentation to Add

**README.md section**:
```markdown
## Backtesting with CSV Data

Set `HISTORICAL_DATA_DIR` environment variable or use default `~/.baretrader/data/historical/`.

CSV format: `{SYMBOL}.csv` with columns: `date, open, high, low, close, volume`
Example: `AAPL.csv`, `MSFT.csv`

For testing, create minimal CSV:
```bash
mkdir -p ~/.baretrader/data/historical
# Add sample CSV files
```
```

**Error message improvement** (`trader/backtest/data.py`):
```python
raise FileNotFoundError(
    f"CSV file not found: {csv_path}. "
    f"Set HISTORICAL_DATA_DIR or create {default_dir}/{{SYMBOL}}.csv. "
    f"See README.md 'Backtesting with CSV Data' section."
)
```

### Acceptance Criteria
- 📝 README documents CSV setup and format
- 📝 Error message includes link to docs
- 🔄 Test: `test_backtest_csv_setup_instructions()` verifies helpful error

### Testing Strategy
```python
# tests/test_backtest_data.py
def test_csv_error_message_helpful():
    """Test that CSV not found error includes setup instructions."""
    with pytest.raises(FileNotFoundError) as exc:
        load_price_data("AAPL", data_source="csv")
    assert "HISTORICAL_DATA_DIR" in str(exc.value)
    assert "README" in str(exc.value)
```

---

## Issue 4: MCP Tools Not Visible in Client 🔴

**Status**: 🔴 **OPEN** — Client configuration / tool discovery

**Priority**: ⭐⭐ (Testing convenience)

### Why This Matters
- **For Testing**: Some tools (`list_scheduled_strategies`, `get_top_movers`) not visible in MCP client (e.g. Cursor)
- **For AI Agents**: Cannot discover all available tools via standard MCP tool list
- **For MCP Server**: All 32+ tools implemented but client may not expose all

### Observed Behavior
- Run 1 verified `list_scheduled_strategies` and `get_top_movers` via direct server import
- MCP client (Cursor) tool list may not include all server tools
- No way to verify tool visibility without manual testing

### Root Cause Analysis
1. **Client configuration**: MCP client may filter or not discover all tools
2. **Tool registration**: Server registers all tools but client discovery may be incomplete
3. **No verification**: No automated check that all server tools appear in client

### Implementation Details

#### Files to Modify
- 📝 `README.md` — Document which tools may require direct invocation for testing
- 🔄 `trader/mcp/server.py` — Verify all tools registered in FastMCP instance
- 📝 `CONTRIBUTING.md` — Note that some tools may need server import for testing
- 🔄 `tests/test_mcp_contract.py` — Consider adding test that lists all registered tools

#### Verification Steps
1. Check `trader/mcp/server.py` exports all tools in FastMCP `mcp.tool()` calls
2. Document in README: "For testing, if tool not in client, use `from baretrader.mcp.server import <tool>`"
3. Add helper script: `scripts/list_mcp_tools.py` to print all registered tools

### Acceptance Criteria
- 📝 README documents tool visibility and workaround
- 🔄 All 32+ tools registered in server
- 📝 Test plan notes which tools verified via server import

### Testing Strategy
```python
# scripts/list_mcp_tools.py
"""List all MCP tools registered in server."""
from baretrader.mcp.server import mcp
for tool in mcp.list_tools():
    print(f"{tool.name}: {tool.description[:60]}...")
```

---

## Summary

| Issue | Status | Priority | Blocker |
|-------|--------|----------|---------|
| Strategy tools fail with `pullback_trailing` | 🔴 OPEN | ⭐⭐⭐⭐⭐ | Yes (all strategy ops) |
| `run_optimization` param keys | 🔴 OPEN | ⭐⭐⭐⭐ | Yes (optimization) |
| CSV data path docs | 🔴 OPEN | ⭐⭐⭐ | No |
| MCP tool visibility | 🔴 OPEN | ⭐⭐ | No |

**Next Steps**:
1. Verify Issue 1 fix after MCP restart
2. Implement Issue 2 normalization (Option A) or document (Option B)
3. Add Issue 3 documentation
4. Document Issue 4 workaround
