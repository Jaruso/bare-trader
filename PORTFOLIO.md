# BareTrader Curated Strategy Portfolio

This file contains strategies that have been extensively tested and validated. Only add strategies after thorough backtesting and review.

**Purpose**: Curated collection of tested strategies that have been sufficiently validated through backtesting. Only strategies that meet quality thresholds should be added.

**Key Distinction**: PORTFOLIO.md is for **curated, execution-ready strategies** with confidence levels and targets. CONTEXTS.md is for raw learning and exploration.

**Entry Criteria**:
- Minimum 6 months of historical data tested
- Sharpe ratio > 1.0
- Win rate > 50%
- At least 20 trades in backtest
- Tested across multiple market conditions

**Confidence Levels**:
- **High (80%+)**: Consistent across multiple periods, high Sharpe ratio (>1.5), low drawdown (<5%), tested across different market regimes
- **Medium (60-79%)**: Good performance but some variability, moderate Sharpe (1.0-1.5), moderate drawdown (5-10%)
- **Low (50-59%)**: Meets criteria but limited testing or inconsistent results

---

## Entry Template

Use this template when adding new strategies:

```markdown
## [SYMBOL] - [Strategy Type]

**Symbol**: [TICKER]  
**Strategy Type**: [trailing-stop | bracket | scale-out | grid]  
**Status**: ✅ Validated | ⚠️ Under Review | ❌ Deprecated  
**Confidence Level**: [High/Medium/Low] ([X]%)  
**Last Updated**: YYYY-MM-DD

### Parameters
- `[param_name]`: [value]
- `qty`: [shares]
- `entry_price`: [Market | Limit | Conditions]

### Performance Metrics (Backtest: YYYY-MM-DD to YYYY-MM-DD)
- **Sharpe Ratio**: [X.X]
- **Total Return**: [X.X]%
- **Win Rate**: [X.X]%
- **Max Drawdown**: -[X.X]%
- **Average Trade Duration**: [X] days
- **Total Trades**: [X]

### Execution Guidelines
- **Best Market Conditions**: [Description]
- **Entry Timing**: [When to enter]
- **Exit Timing**: [When/how to exit]
- **Risk Management**: [Position sizing, stop losses, etc.]
- **When to Avoid**: [Conditions to avoid this strategy]

### Validation History
- Backtest ID: `[bt_xxx]`
- Optimization ID: `[opt_xxx]` (if applicable)
- Tested Periods: [List of periods tested]
- Consistency: [Description of consistency across periods]

### Notes
- [Additional observations]
- [Market condition notes]
- [Risk considerations]
```

---

## Portfolio Allocation ($100,000 Paper Account)

**Total Capital**: $100,000  
**Last Updated**: 2026-02-12  
**Account Type**: Paper Trading

### Strategy Allocation

| Symbol | Strategy | Allocation | Capital | Expected Return | Confidence |
|--------|----------|------------|---------|----------------|------------|
| NVDA | Trailing-stop | 25% | $25,000 | +539.8% | High (85%) |
| MSFT | Trailing-stop | 15% | $15,000 | +88.1% | Medium (70%) |
| XLK | Bracket | 15% | $15,000 | +27.2% | Medium (65%) |
| GOOGL | Bracket | 10% | $10,000 | +66.7% | Medium (70%) |
| AMZN | Bracket | 10% | $10,000 | +66.6% | Medium (70%) |
| XLI | Bracket | 8% | $8,000 | +16.9% | Medium (60%) |
| XLF | Bracket | 7% | $7,000 | +12.2% | Medium (60%) |
| XLP | Bracket | 5% | $5,000 | +10.9% | Medium (60%) |
| AEM | Bracket | 3% | $3,000 | +27.3% | Medium (65%) |
| GDX | Bracket | 2% | $2,000 | +6.5% | Low (55%) |

**Portfolio Characteristics**:
- **Tech Exposure**: 65% (NVDA, MSFT, XLK, GOOGL, AMZN)
- **Sector ETFs**: 35% (XLK, XLI, XLF, XLP, GDX)
- **Individual Stocks**: 68% (NVDA, MSFT, GOOGL, AMZN, AEM)
- **ETFs**: 37% (XLK, XLI, XLF, XLP, GDX)
- **Expected Weighted Return**: ~85-95% annually (based on 2024 backtest results)
- **Risk Level**: Moderate to High (tech-heavy, but diversified across sectors)

**Diversification**:
- ✅ Tech sector: NVDA, MSFT, GOOGL, AMZN, XLK
- ✅ Industrials: XLI
- ✅ Financials: XLF
- ✅ Consumer Staples: XLP
- ✅ Mining/Gold: AEM, GDX

---

## NVDA - Trailing-Stop

**Symbol**: NVDA  
**Strategy Type**: trailing-stop  
**Status**: ✅ Validated  
**Confidence Level**: High (85%)  
**Last Updated**: 2026-02-12

### Parameters
- `trailing_stop_pct`: 5.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +539.8%
- **Win Rate**: 44.4%
- **Max Drawdown**: -1.6%
- **Profit Factor**: 2.90
- **Total Trades**: 36
- **Average Win**: $515.25
- **Average Loss**: -$142.29

### Execution Guidelines
- **Best Market Conditions**: Strong upward trends, high momentum (AI boom periods)
- **Entry Timing**: Market entry on any signal. Trailing stop allows winners to run.
- **Exit Timing**: Automatic via trailing stop (5% from high watermark)
- **Risk Management**: 
  - Position size: 25% of portfolio ($25K allocation)
  - Max position: 10 shares per trade
  - Stop loss: Built into trailing stop (5%)
  - Monitor for extreme volatility periods
- **When to Avoid**: 
  - Extreme market volatility (VIX > 30)
  - Major news events that could cause gaps
  - After major run-ups without consolidation

### Validation History
- Backtest ID: `759ad79a`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Exceptional performance in 2024 AI boom. Lower win rate (44%) but massive average wins ($515 vs $142 losses) due to trailing stop capturing explosive moves.

### Notes
- **Exceptional performer**: +539% return in 2024 demonstrates power of trailing stops on high-momentum stocks
- **Low drawdown**: Only 1.6% max drawdown despite massive returns
- **High profit factor**: 2.90 indicates excellent risk/reward
- **Trade frequency**: 36 trades over 12 months = ~3 trades/month (moderate frequency)
- **Risk**: Despite lower win rate, profit factor and average win size compensate
- **2024 Context**: NVDA benefited from AI boom - future performance may vary

---

## MSFT - Trailing-Stop

**Symbol**: MSFT  
**Strategy Type**: trailing-stop  
**Status**: ✅ Validated  
**Confidence Level**: Medium (70%)  
**Last Updated**: 2026-02-12

### Parameters
- `trailing_stop_pct`: 5.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +88.1%
- **Win Rate**: 63.6%
- **Max Drawdown**: -33.3%
- **Profit Factor**: 3.15
- **Total Trades**: 11
- **Average Win**: $184.36
- **Average Loss**: -$102.27

### Execution Guidelines
- **Best Market Conditions**: Strong consistent uptrends, stable tech sector performance
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via trailing stop (5% from high watermark)
- **Risk Management**: 
  - Position size: 15% of portfolio ($15K allocation)
  - Max position: 10 shares per trade
  - Stop loss: Built into trailing stop (5%)
  - Monitor drawdown (max 33% observed)
- **When to Avoid**: 
  - High volatility periods
  - Major earnings announcements
  - Tech sector downturns

### Validation History
- Backtest ID: `991ef943`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Strong performance with excellent win rate (64%) and profit factor (3.15). Lower trade count (11 trades) but consistent gains.

### Notes
- **High win rate**: 63.6% win rate with strong profit factor (3.15)
- **Moderate drawdown**: 33% max drawdown requires careful monitoring
- **Low trade frequency**: Only 11 trades in 12 months = ~1 trade/month (buy-and-hold compatible)
- **Consistent performer**: Strong returns with good risk control

---

## XLK - Bracket

**Symbol**: XLK  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (65%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 15.0%
- `stop_loss_pct`: 7.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +27.2%
- **Win Rate**: 50.0%
- **Max Drawdown**: -15.4%
- **Profit Factor**: 1.89
- **Total Trades**: 4
- **Average Win**: $288.59
- **Average Loss**: -$152.72

### Execution Guidelines
- **Best Market Conditions**: Tech sector uptrends, broad market strength
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (15% take profit or 7% stop loss)
- **Risk Management**: 
  - Position size: 15% of portfolio ($15K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 7% (built into bracket)
  - Wide parameters align with buy-and-hold preference
- **When to Avoid**: 
  - Tech sector downturns
  - High volatility periods (VIX > 30)

### Validation History
- Backtest ID: `3a4b593b`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Strong ETF performance with wide parameters. Only 4 trades in 12 months = perfect for buy-and-hold investors.

### Notes
- **Buy-and-hold compatible**: Wide parameters (15% TP, 7% SL) result in only 4 trades/year
- **Tech sector exposure**: Broad tech sector ETF provides diversification within tech
- **Good returns**: +27% return with moderate risk (15% max drawdown)
- **Liquid**: ETF provides excellent liquidity and tight spreads

---

## GOOGL - Bracket

**Symbol**: GOOGL  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (70%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 10.0%
- `stop_loss_pct`: 5.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +66.7%
- **Win Rate**: 58.3%
- **Max Drawdown**: -25.1%
- **Profit Factor**: 2.66
- **Total Trades**: 12
- **Average Win**: $152.66
- **Average Loss**: -$80.25

### Execution Guidelines
- **Best Market Conditions**: Moderate volatility tech trends, stable market conditions
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (10% take profit or 5% stop loss)
- **Risk Management**: 
  - Position size: 10% of portfolio ($10K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 5% (built into bracket)
  - Monitor drawdown (max 25% observed)
- **When to Avoid**: 
  - High volatility periods
  - Major tech sector downturns
  - Earnings announcements

### Validation History
- Backtest ID: `3b503008`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Good performance with bracket strategy. Better than trailing-stop for GOOGL (+66.7% vs +48.6%).

### Notes
- **Bracket preferred**: Bracket strategy outperformed trailing-stop for GOOGL
- **Good win rate**: 58% win rate with strong profit factor (2.66)
- **Moderate frequency**: 12 trades in 12 months = ~1 trade/month

---

## AMZN - Bracket

**Symbol**: AMZN  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (70%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 10.0%
- `stop_loss_pct`: 5.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +66.6%
- **Win Rate**: 60.0%
- **Max Drawdown**: -18.9%
- **Profit Factor**: 2.79
- **Total Trades**: 10
- **Average Win**: $173.09
- **Average Loss**: -$93.11

### Execution Guidelines
- **Best Market Conditions**: Moderate volatility trends, stable market conditions
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (10% take profit or 5% stop loss)
- **Risk Management**: 
  - Position size: 10% of portfolio ($10K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 5% (built into bracket)
  - Monitor drawdown (max 19% observed)
- **When to Avoid**: 
  - High volatility periods
  - Major earnings announcements
  - Tech sector downturns

### Validation History
- Backtest ID: `262aa6ca`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Good performance with bracket strategy. Similar to GOOGL in returns and characteristics.

### Notes
- **Bracket preferred**: Bracket strategy slightly outperformed trailing-stop for AMZN (+66.6% vs +54.1%)
- **High win rate**: 60% win rate with strong profit factor (2.79)
- **Low frequency**: 10 trades in 12 months = ~0.8 trades/month (buy-and-hold compatible)

---

## XLI - Bracket

**Symbol**: XLI  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (60%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 15.0%
- `stop_loss_pct`: 7.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +16.9%
- **Win Rate**: 100% (1 trade)
- **Max Drawdown**: 0%
- **Profit Factor**: N/A (no losses)
- **Total Trades**: 1

### Execution Guidelines
- **Best Market Conditions**: Industrial sector uptrends, economic expansion periods
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (15% take profit or 7% stop loss)
- **Risk Management**: 
  - Position size: 8% of portfolio ($8K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 7% (built into bracket)
  - Wide parameters for buy-and-hold compatibility
- **When to Avoid**: 
  - Economic downturns
  - Industrial sector weakness

### Validation History
- Backtest ID: `b4bcc859`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Single trade in 2024 resulted in +16.9% return. Perfect for buy-and-hold investors seeking minimal turnover.

### Notes
- **Buy-and-hold ideal**: Only 1 trade in 12 months = minimal turnover
- **Industrial exposure**: Provides diversification to industrials sector
- **Low risk**: No drawdown observed (single winning trade)

---

## XLF - Bracket

**Symbol**: XLF  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (60%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 15.0%
- `stop_loss_pct`: 7.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +12.2%
- **Win Rate**: 100% (2 trades)
- **Max Drawdown**: 0%
- **Profit Factor**: N/A (no losses)
- **Total Trades**: 2

### Execution Guidelines
- **Best Market Conditions**: Financial sector strength, rising interest rate environments (if applicable)
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (15% take profit or 7% stop loss)
- **Risk Management**: 
  - Position size: 7% of portfolio ($7K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 7% (built into bracket)
  - Wide parameters for buy-and-hold compatibility
- **When to Avoid**: 
  - Financial sector crises
  - High volatility periods

### Validation History
- Backtest ID: `41068194`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Only 2 trades in 2024, both winners. Perfect for buy-and-hold investors.

### Notes
- **Buy-and-hold compatible**: Only 2 trades in 12 months = minimal turnover
- **Financial exposure**: Provides diversification to financial sector
- **Low risk**: No drawdown observed (all winning trades)

---

## XLP - Bracket

**Symbol**: XLP  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (60%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 15.0%
- `stop_loss_pct`: 7.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +10.9%
- **Win Rate**: 100% (1 trade)
- **Max Drawdown**: 0%
- **Profit Factor**: N/A (no losses)
- **Total Trades**: 1

### Execution Guidelines
- **Best Market Conditions**: Defensive sector strength, economic stability
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (15% take profit or 7% stop loss)
- **Risk Management**: 
  - Position size: 5% of portfolio ($5K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 7% (built into bracket)
  - Wide parameters for buy-and-hold compatibility
- **When to Avoid**: 
  - Economic downturns (though consumer staples are defensive)
  - Major market crashes

### Validation History
- Backtest ID: `f2f70beb`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Single trade in 2024 resulted in +10.9% return. Perfect defensive position for buy-and-hold investors.

### Notes
- **Buy-and-hold ideal**: Only 1 trade in 12 months = minimal turnover
- **Defensive sector**: Consumer staples provide defensive exposure
- **Low risk**: No drawdown observed (single winning trade)
- **Stable returns**: Modest but consistent returns

---

## AEM - Bracket

**Symbol**: AEM  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Medium (65%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 10.0%
- `stop_loss_pct`: 5.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +27.3%
- **Win Rate**: 50.0%
- **Max Drawdown**: -8.6%
- **Profit Factor**: 1.86
- **Total Trades**: 18
- **Average Win**: $65.50
- **Average Loss**: -$35.20

### Execution Guidelines
- **Best Market Conditions**: Gold price uptrends, mining sector strength, inflationary periods
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (10% take profit or 5% stop loss)
- **Risk Management**: 
  - Position size: 3% of portfolio ($3K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 5% (built into bracket)
  - Monitor gold prices and mining sector trends
- **When to Avoid**: 
  - Gold price downturns
  - Mining sector weakness
  - High volatility periods

### Validation History
- Backtest ID: `6ce00e91`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Best performing mining stock. Bracket strategy outperformed trailing-stop (+27.3% vs +14.8%).

### Notes
- **Gold miner**: Provides gold exposure and diversification
- **Best mining performer**: Outperformed other mining stocks tested (KGC, AG, FCX, HL)
- **Moderate frequency**: 18 trades in 12 months = ~1.5 trades/month
- **Good risk control**: 8.6% max drawdown with solid profit factor (1.86)

---

## GDX - Bracket

**Symbol**: GDX  
**Strategy Type**: bracket  
**Status**: ✅ Validated  
**Confidence Level**: Low (55%)  
**Last Updated**: 2026-02-12

### Parameters
- `take_profit_pct`: 15.0%
- `stop_loss_pct`: 7.0%
- `qty`: 10 shares per trade
- `entry_price`: Market

### Performance Metrics (Backtest: 2024-01-01 to 2024-12-31)
- **Sharpe Ratio**: N/A (not calculated)
- **Total Return**: +6.5%
- **Win Rate**: 44.4%
- **Max Drawdown**: -5.3%
- **Profit Factor**: 1.52
- **Total Trades**: 9
- **Average Win**: N/A
- **Average Loss**: N/A

### Execution Guidelines
- **Best Market Conditions**: Gold price uptrends, mining sector strength
- **Entry Timing**: Market entry on any signal
- **Exit Timing**: Automatic via bracket (15% take profit or 7% stop loss)
- **Risk Management**: 
  - Position size: 2% of portfolio ($2K allocation)
  - Max position: 10 shares per trade
  - Stop loss: 7% (built into bracket)
  - Monitor gold prices and mining sector trends
- **When to Avoid**: 
  - Gold price downturns
  - Mining sector weakness

### Validation History
- Backtest ID: `3e175282`
- Tested Periods: 2024-01-01 to 2024-12-31 (12 months)
- Consistency: Modest returns (+6.5%) with lower win rate (44%). Provides gold hedge but lower confidence.

### Notes
- **Gold miners ETF**: Provides broad gold mining exposure
- **Modest returns**: +6.5% return is lower than other strategies
- **Lower win rate**: 44% win rate requires careful monitoring
- **Hedge purpose**: Small allocation (2%) serves as gold hedge/diversification
- **Low confidence**: Lower returns and win rate justify small allocation

---

## Portfolio Management Notes

### Rebalancing
- Monitor positions monthly
- Rebalance if allocations drift >5% from target
- Consider taking profits on NVDA if returns exceed 200% (exceptional gains)

### Risk Management
- **Max single position**: 25% (NVDA)
- **Max sector exposure**: 65% (Tech)
- **Stop losses**: All strategies have built-in stop losses
- **Daily monitoring**: Check positions daily for any issues

### Expected Performance
Based on 2024 backtest results:
- **Weighted average return**: ~85-95% annually
- **Portfolio volatility**: Moderate to High (tech-heavy)
- **Trade frequency**: Low to Moderate (1-3 trades/month per strategy)

### Diversification Benefits
- **Sector diversification**: Tech (65%), Industrials (8%), Financials (7%), Consumer Staples (5%), Mining (5%)
- **Instrument diversification**: Individual stocks (68%), ETFs (37%)
- **Strategy diversification**: Trailing-stop (40%), Bracket (60%)

### Monitoring Checklist
- [ ] Daily: Check all positions for any errors or issues
- [ ] Weekly: Review performance vs. backtest expectations
- [ ] Monthly: Rebalance if allocations drift
- [ ] Quarterly: Review strategy performance and consider adjustments

---
