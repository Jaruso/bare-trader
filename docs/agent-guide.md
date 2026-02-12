# AutoTrader Agent Guide

Comprehensive guide for AI agents using the AutoTrader MCP server to explore trading strategies, run backtests, and build a portfolio of validated strategies.

---

## Getting Started

### MCP Connection Setup

AutoTrader provides an MCP-compliant server with 28 tools accessible via stdio transport.

**For Claude Desktop**: Configure in `claude_desktop_config.json`:
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

**For Cursor**: MCP tools are available when the AutoTrader MCP server is configured.

### Verify Connection

Start by calling `get_status()` to verify the MCP server is accessible and check engine status.

---

## Tool Reference

AutoTrader provides 31 MCP tools organized by category:

### Engine Tools
- `get_status()` - Get engine status, environment, active strategies
- `stop_engine(force: bool)` - Stop running engine

### Portfolio & Market Data
- `get_balance()` - Account balance, equity, buying power, daily P/L
- `get_positions()` - Open positions with prices and unrealized P/L
- `get_portfolio()` - Full portfolio summary
- `get_quote(symbol: str)` - Current bid/ask/last for symbol
- `get_top_movers(market_type="stocks", limit=10)` - Today's top gainers and losers from Alpaca screener API

### Orders
- `place_order(symbol, qty, side, price)` - Place limit order
- `list_orders(show_all: bool)` - List orders (open or all)
- `cancel_order(order_id: str)` - Cancel open order

### Strategies
- `list_strategies()` - List all configured strategies
- `get_strategy(strategy_id: str)` - Get strategy details
- `create_strategy(strategy_type, symbol, qty=1, ...)` - Create strategy
- `remove_strategy(strategy_id: str)` - Delete strategy
- `pause_strategy(strategy_id: str)` - Pause strategy
- `resume_strategy(strategy_id: str)` - Resume strategy
- `set_strategy_enabled(strategy_id, enabled: bool)` - Enable/disable
- `schedule_strategy(strategy_id, schedule_at: str)` - Schedule strategy to start at specific time
- `list_scheduled_strategies()` - List all scheduled strategies
- `cancel_schedule(strategy_id: str)` - Cancel scheduled strategy

### Backtesting
- `run_backtest(strategy_type, symbol, start, end, ...)` - Run backtest
- `list_backtests()` - List saved backtests
- `show_backtest(backtest_id: str)` - Get detailed results
- `compare_backtests(backtest_ids: list[str])` - Compare multiple backtests
- `delete_backtest(backtest_id: str)` - Delete saved backtest

### Analysis
- `analyze_performance(symbol=None, days=30, limit=1000)` - Performance metrics
- `get_trade_history(symbol=None, limit=20)` - Recent trade records
- `get_today_pnl()` - Today's realized P/L

### Indicators
- `list_indicators()` - List available indicators
- `describe_indicator(name: str)` - Get indicator details

### Optimization
- `run_optimization(strategy_type, symbol, start, end, params, ...)` - Parameter optimization

### Safety
- `get_safety_status()` - Safety check status and limits

See [CLI and MCP Usage by Feature](cli-mcp-usage.md) for detailed parameter descriptions.

---

## Common Workflows

### Backtesting Workflow

1. **Run Initial Backtest**
   - Call `run_backtest()` with strategy parameters
   - Use at least 6 months of historical data
   - Test on different symbols and time periods

2. **Analyze Results**
   - Call `show_backtest()` to get detailed metrics
   - Extract key metrics: Sharpe ratio, total return %, win rate, max drawdown
   - Compare multiple runs with `compare_backtests()`

3. **Document Learnings**
   - Record findings in CONTEXTS.md
   - Note patterns, surprises, and insights
   - Document questions explored and answers found

4. **Optimize Parameters**
   - Use `run_optimization()` to find optimal parameters
   - Test best parameters across multiple time periods
   - Validate consistency before considering for PORTFOLIO.md

### Strategy Optimization Workflow

1. **Define Parameter Grid**
   - Identify parameters to optimize (e.g., `trailing_pct: [2.0, 2.5, 3.0]`)
   - Choose objective metric (e.g., `total_return_pct`, `sharpe_ratio`, `win_rate`)

2. **Run Optimization**
   - Call `run_optimization()` with parameter grid
   - Use grid search or random search method
   - Test across sufficient historical period (6+ months)

3. **Validate Results**
   - Test best parameters on different time periods
   - Check consistency across market conditions
   - Document optimal configurations in CONTEXTS.md

### Portfolio Curation Workflow

1. **Review CONTEXTS.md**
   - Identify strategies with multiple successful backtests
   - Look for consistent performance across time periods
   - Note strategies that meet quality thresholds

2. **Validate Entry Criteria**
   - Minimum 6 months historical data: ✅
   - Sharpe ratio > 1.0: ✅
   - Win rate > 50%: ✅
   - At least 20 trades: ✅
   - Tested across market conditions: ✅

3. **Calculate Confidence Level**
   - High (80%+): Consistent, high Sharpe (>1.5), low drawdown (<5%)
   - Medium (60-79%): Good but some variability
   - Low (50-59%): Meets criteria but limited testing

4. **Document Execution Guidelines**
   - Best market conditions for entry
   - Entry timing recommendations
   - Risk management guidelines
   - When to avoid this strategy

5. **Add to PORTFOLIO.md**
   - Format according to PORTFOLIO.md structure
   - Include all required sections
   - Link to backtest IDs for traceability

---

## Learning and Documentation

### CONTEXTS.md vs PORTFOLIO.md

**CONTEXTS.md** - Learning and Discovery Log:
- **Purpose**: Raw discoveries, experiments, patterns observed
- **When to use**: Document all backtests, explorations, learnings
- **Format**: Append-only, date-formatted entries
- **Content**: What agents learn during exploration

**PORTFOLIO.md** - Curated Strategy Portfolio:
- **Purpose**: Validated, execution-ready strategies
- **When to use**: Only after extensive backtesting and review
- **Format**: Structured entries with confidence levels
- **Content**: Strategies that meet quality thresholds

**Key Distinction**: CONTEXTS.md = "What we're learning", PORTFOLIO.md = "What we're confident in"

### Documenting in CONTEXTS.md

For each exploration session, document:
- Date and agent type
- Activity description
- Tools used
- Learnings and discoveries
- Successful strategy tests (if any)
- Questions explored and answers found
- Insights and patterns

### Adding to PORTFOLIO.md

Only add strategies that:
- Have been extensively backtested (6+ months data)
- Meet quality thresholds (Sharpe > 1.0, win rate > 50%, etc.)
- Show consistent performance across multiple periods
- Have clear execution guidelines

---

## Portfolio Curation

### Entry Criteria

Before adding a strategy to PORTFOLIO.md, verify:
- ✅ Minimum 6 months of historical data tested
- ✅ Sharpe ratio > 1.0
- ✅ Win rate > 50%
- ✅ At least 20 trades in backtest
- ✅ Tested across multiple market conditions

### Confidence Level Calculation

**High (80%+)**:
- Consistent performance across multiple periods
- Sharpe ratio > 1.5
- Max drawdown < 5%
- Tested across different market regimes (trending, ranging, volatile)

**Medium (60-79%)**:
- Good performance but some variability
- Sharpe ratio 1.0-1.5
- Max drawdown 5-10%
- Limited testing across market conditions

**Low (50-59%)**:
- Meets basic criteria
- Limited testing or inconsistent results
- Requires more validation before confidence increases

### Execution Guidelines

For each PORTFOLIO.md entry, document:
- Best market conditions for entry
- Entry timing recommendations
- Exit timing/strategy
- Risk management guidelines
- When to avoid this strategy

---

## Non-Financial User Guidance

### Helping Users Ask Sophisticated Questions

As an agent, help non-financial users by:

1. **Explaining Financial Concepts**
   - Explain what Sharpe ratio means (risk-adjusted returns)
   - Explain win rate vs total return
   - Explain drawdown and risk

2. **Guiding Exploration**
   - Start broad: "What strategies work for AAPL?"
   - Narrow down: "Which has lowest risk?"
   - Optimize: "What's the best trailing stop percentage?"

3. **Testing Systematically**
   - Test all strategy types on same symbol
   - Test same strategy across different symbols
   - Test across different time periods
   - Test parameter variations

4. **Providing Context**
   - Compare results to benchmarks
   - Explain market conditions
   - Highlight risks and limitations

### Example Workflows for Non-Financial Users

**"I want to trade AAPL safely"**:
1. Test all strategy types on AAPL
2. Focus on strategies with low drawdown
3. Compare win rates and Sharpe ratios
4. Recommend safest option with execution guidelines

**"What's the best strategy for steady returns?"**:
1. Test strategies focusing on Sharpe ratio
2. Look for consistent performance
3. Avoid high-volatility strategies
4. Document findings in CONTEXTS.md

---

## Best Practices

### Error Handling

- Always check `get_status()` before operations
- Handle rate limits gracefully (backtest/optimization tools)
- Respect timeout limits for long-running operations
- Check error responses for actionable guidance

### Rate Limits and Timeouts

- `run_backtest()`: Subject to `MCP_BACKTEST_TIMEOUT_SECONDS` (default 300s)
- `run_optimization()`: Subject to `MCP_OPTIMIZATION_TIMEOUT_SECONDS` (default 600s)
- Long-running tools: Rate limited to `MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE` (default 10)

### Data Requirements

- Use at least 6 months of historical data for meaningful backtests
- Test across multiple market conditions when possible
- Use `data_source: "alpaca"` for live data or `"csv"` for local files

### Documentation

- Always document learnings in CONTEXTS.md
- Link backtest IDs for traceability
- Update PORTFOLIO.md only after thorough validation
- Keep entries structured and parseable

---

## Examples

### Example 1: Comprehensive Backtest Exploration

```
1. Call get_status() to verify connection
2. Call list_strategies() to see available strategies
3. Call run_backtest("trailing-stop", "AAPL", "2024-01-01", "2024-12-31", trailing_pct=2.5)
4. Call show_backtest(backtest_id) to get detailed results
5. Extract metrics: Sharpe ratio, return %, win rate
6. Document in CONTEXTS.md with date, tools used, learnings
```

### Example 2: Strategy Optimization

```
1. Call run_optimization("trailing-stop", "AAPL", "2024-01-01", "2024-12-31", 
   params={"trailing_pct": [2.0, 2.5, 3.0]}, objective="sharpe_ratio")
2. Analyze optimization results
3. Test best parameters on different period: run_backtest(..., start="2023-06-01", end="2024-05-31")
4. Validate consistency
5. Document optimal configuration in CONTEXTS.md
```

### Example 3: Portfolio Curation

```
1. Review CONTEXTS.md for strategies with multiple successful backtests
2. Validate entry criteria for a promising strategy
3. Calculate confidence level based on consistency
4. Document execution guidelines
5. Add formatted entry to PORTFOLIO.md with all required sections
```

---

## Reference

- [CLI and MCP Usage by Feature](cli-mcp-usage.md) - Detailed tool reference
- [CONTEXTS.md](../CONTEXTS.md) - Learning and discovery log
- [PORTFOLIO.md](../PORTFOLIO.md) - Curated strategy portfolio
- [README.md](../README.md) - User documentation
- [PLAN.md](../PLAN.md) - Development roadmap

---
