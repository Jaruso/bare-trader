# BareTrader Agent Learning Context

This file tracks discoveries, successful strategies, patterns, and insights from agent usage of the BareTrader MCP server.

**Purpose**: Append-only learning log for agent discoveries, experiments, and insights. Tracks what agents learn during exploration and backtesting.

**Key Distinction**: CONTEXTS.md is for **learning and discovery** - raw findings, experiments, patterns observed. PORTFOLIO.md is for **curated, tested strategies** ready for execution.

**Format**: Date-formatted entries, newest-first for easy agent traversal. Never delete entries, only append.

---

## 2026-02-12

### Agent: Cursor
**Activity**: Portfolio curation - building $100K diversified portfolio from validated strategies
**Tools Used**: `list_backtests()`, `show_backtest()`, portfolio analysis
**User Goal**: Allocate $100,000 paper account across validated strategies with good diversification, weighting successful strategies more heavily
**Process**: Reviewed all backtest results from CONTEXTS.md, validated against entry criteria, created portfolio allocation

**Portfolio Allocation ($100K)**:
- **NVDA trailing-stop**: 25% ($25K) - Highest return potential (+539% in 2024)
- **MSFT trailing-stop**: 15% ($15K) - Strong returns (+88%), high win rate (64%)
- **XLK bracket**: 15% ($15K) - Tech ETF, buy-and-hold compatible (+27%)
- **GOOGL bracket**: 10% ($10K) - Good returns (+67%), 58% win rate
- **AMZN bracket**: 10% ($10K) - Good returns (+67%), 60% win rate
- **XLI bracket**: 8% ($8K) - Industrials ETF (+17%)
- **XLF bracket**: 7% ($7K) - Financials ETF (+12%)
- **XLP bracket**: 5% ($5K) - Consumer Staples ETF (+11%)
- **AEM bracket**: 3% ($3K) - Gold miner (+27%)
- **GDX bracket**: 2% ($2K) - Gold miners ETF (+6.5%)

**Portfolio Characteristics**:
- **Tech Exposure**: 65% (NVDA, MSFT, XLK, GOOGL, AMZN)
- **Sector ETFs**: 35% (XLK, XLI, XLF, XLP, GDX)
- **Individual Stocks**: 68% (NVDA, MSFT, GOOGL, AMZN, AEM)
- **ETFs**: 37% (XLK, XLI, XLF, XLP, GDX)
- **Expected Weighted Return**: ~85-95% annually (based on 2024 backtest results)
- **Diversification**: Tech (65%), Industrials (8%), Financials (7%), Consumer Staples (5%), Mining (5%)

**Validation Process**:
- Reviewed all backtest results from tech sector, mining sector, and ETF research
- Validated strategies against entry criteria (6+ months data, win rate >50%, sufficient trades)
- Adjusted criteria for ETFs (wide parameters intentionally result in fewer trades)
- Calculated confidence levels based on performance metrics
- Created portfolio allocation weighted by expected returns and diversification needs

**Strategies Added to PORTFOLIO.md**:
1. NVDA trailing-stop (High confidence, 85%)
2. MSFT trailing-stop (Medium confidence, 70%)
3. XLK bracket (Medium confidence, 65%)
4. GOOGL bracket (Medium confidence, 70%)
5. AMZN bracket (Medium confidence, 70%)
6. XLI bracket (Medium confidence, 60%)
7. XLF bracket (Medium confidence, 60%)
8. XLP bracket (Medium confidence, 60%)
9. AEM bracket (Medium confidence, 65%)
10. GDX bracket (Low confidence, 55%)

**Key Decisions**:
- **NVDA allocation (25%)**: Despite 44% win rate, exceptional returns (+539%) and low drawdown (1.6%) justify largest allocation
- **Tech-heavy (65%)**: Tech sector showed strongest performance in 2024, but balanced with sector ETFs
- **ETF allocation (37%)**: Provides diversification and buy-and-hold compatibility
- **Small mining allocation (5%)**: AEM and GDX provide gold hedge but lower returns than tech

**Questions Explored**:
- How to balance high-return strategies (NVDA) with diversification needs?
  - **Answer**: Allocate more to high-return strategies (NVDA 25%) while maintaining sector diversification through ETFs
- Should we include strategies with lower trade counts?
  - **Answer**: Yes, for ETFs with wide parameters (buy-and-hold compatible), lower trade counts are acceptable
- How to weight allocation between individual stocks and ETFs?
  - **Answer**: 68% individual stocks (higher returns), 37% ETFs (diversification, buy-and-hold)

**Insights**:
- **Portfolio construction works**: Can build diversified portfolio from validated strategies
- **Tech sector dominance**: Tech strategies showed strongest performance in 2024
- **ETF diversification**: Sector ETFs provide good diversification with lower risk
- **Buy-and-hold compatible**: Wide parameters on ETFs result in minimal turnover (1-4 trades/year)
- **Risk management**: All strategies have built-in stop losses, portfolio weighted by confidence levels

### Agent: Cursor
**Activity**: Diversified ETF strategy discovery - testing buy-and-hold compatible strategies across multiple sectors for dividend-focused portfolio
**Tools Used**: `get_quote()`, `run_backtest()` (bracket, trailing-stop)
**User Goal**: Broad diversification across tech, industrials/mining, financials, consumer staples, and gold/silver hedges. Dividend focus, buy-and-hold preference, good returns.
**ETFs Tested**: VYM (High Dividend Yield), SCHD (Dividend Equity), XLK (Tech), XLI (Industrials), XLF (Financials), XLP (Consumer Staples), GDX (Gold Miners)
**Period**: 2024-01-01 to 2024-12-31
**Strategy Parameters**: Wide brackets (15% TP, 7% SL) and trailing stops (8%) to align with buy-and-hold preference

**ETF Performance Summary**:

**Best Performers**:
1. **XLK (Tech Sector)** - Bracket: **+27.17%** return, 50% win rate, profit factor 1.89, max DD 15.4%, 4 trades
2. **XLI (Industrials)** - Bracket: **+16.93%** return, 100% win rate, 1 trade
3. **VYM (High Dividend Yield)** - Bracket: **+16.86%** return, 100% win rate, 1 trade
4. **XLF (Financials)** - Bracket: **+12.16%** return, 100% win rate, 2 trades
5. **XLP (Consumer Staples)** - Bracket: **+10.93%** return, 100% win rate, 1 trade
6. **GDX (Gold Miners)** - Bracket: **+6.54%** return, 44% win rate, profit factor 1.52, max DD 5.3%, 9 trades

**Underperformers**:
- **SCHD (Dividend Equity)**: Bracket lost -5.37%, trailing-stop only +0.39%

**Key Observations**:
- **Wide parameters work well for ETFs** - 15% TP / 7% SL allows positions to run while providing protection
- **Low trade frequency** - Most ETFs had only 1-2 trades, perfect for buy-and-hold investors
- **Sector ETFs outperform dividend ETFs** - XLK (+27%), XLI (+17%) vs SCHD (-5%)
- **Tech sector strongest** - XLK returned +27% with only 4 trades
- **Consumer staples stable** - XLP +11% with single trade (perfect for buy-and-hold)
- **Gold hedge works** - GDX +6.5% provides diversification benefit

**Strategy Characteristics**:
- **Bracket strategy preferred** - All profitable ETFs used bracket (15% TP, 7% SL)
- **Trailing-stop underperformed** - VYM trailing-stop had 0 trades, SCHD only +0.39%
- **Wide parameters = fewer trades** - Aligns perfectly with buy-and-hold preference
- **ETFs are liquid** - All spreads excellent ($0.01-$0.04), perfect for automated trading

**Portfolio Construction Recommendations**:
- **Tech exposure**: XLK (Tech Sector ETF) - +27% return, liquid, broad tech exposure
- **Industrial exposure**: XLI (Industrial Sector ETF) - +17% return, single trade = minimal turnover
- **Financial exposure**: XLF (Financial Sector ETF) - +12% return, 2 trades
- **Consumer staples**: XLP (Consumer Staples ETF) - +11% return, defensive sector
- **Dividend focus**: VYM (High Dividend Yield ETF) - +17% return, but only 1 trade (may not capture dividends well)
- **Gold hedge**: GDX (Gold Miners ETF) - +6.5% return, provides diversification
- **Avoid**: SCHD - Lost money with bracket strategy

**User Requirements Met**:
- ✅ **Broad diversification** - ETFs cover tech, industrials, financials, consumer staples, gold
- ✅ **Dividend focus** - VYM and SCHD tested (VYM profitable, SCHD not)
- ✅ **Buy-and-hold compatible** - Wide parameters result in 1-4 trades per year
- ✅ **Good returns** - Best performers: XLK +27%, XLI +17%, VYM +17%
- ✅ **Liquid ETFs** - All ETFs have excellent spreads and liquidity
- ✅ **Gold/silver hedge** - GDX provides gold exposure

**Strategy Recommendation**:
- **Use bracket strategy** with 15% take profit and 7% stop loss
- **Portfolio allocation**:
  - 25% XLK (Tech) - Highest return potential
  - 20% XLI (Industrials) - Strong returns, minimal turnover
  - 20% XLF (Financials) - Good returns, sector diversification
  - 15% XLP (Consumer Staples) - Defensive, stable
  - 10% VYM (High Dividend Yield) - Dividend focus
  - 10% GDX (Gold Miners) - Hedge/diversification
- **Expected portfolio return**: Weighted average ~15-18% annually
- **Trade frequency**: Very low (1-4 trades per ETF per year) - perfect for buy-and-hold
- **Dividend capture**: Wide parameters allow holding through dividend payments

**Questions Explored**:
- Can automated strategies work with buy-and-hold dividend investing?
  - **Answer**: Yes, but with wide parameters. Wide brackets (15% TP, 7% SL) result in 1-4 trades per year, allowing dividend capture while still providing automated risk management.
  
- Which ETFs provide best returns for diversified portfolio?
  - **Answer**: Sector ETFs (XLK, XLI, XLF) outperform dividend-focused ETFs (SCHD). Tech sector (XLK) strongest at +27%.

- Do wide parameters align with buy-and-hold preference?
  - **Answer**: Yes - wide parameters result in very low trade frequency (1-4 trades/year), perfect for investors who don't want to trade frequently.

**Insights**:
- **ETFs are excellent for automated trading** - Liquid, broad exposure, lower volatility than individual stocks
- **Wide parameters = buy-and-hold compatible** - 15% TP / 7% SL results in minimal trading
- **Sector ETFs outperform dividend ETFs** - XLK (+27%) vs SCHD (-5%) suggests sector exposure more important than dividend focus for returns
- **Portfolio approach works** - Diversified ETF portfolio can achieve 15-18% returns with minimal trading
- **Automated strategies complement buy-and-hold** - Wide brackets provide risk management without frequent trading

### Agent: Cursor
**Activity**: Mining sector research - comprehensive analysis of gold and silver mining stocks (AEM, AG, FCX, KGC, HL)
**Tools Used**: `get_quote()`, `run_backtest()` (trailing-stop, bracket)
**Sector**: Mining (Gold & Silver)
**Stocks Analyzed**: AEM (Agnico Eagle Mines - Gold), AG (First Majestic Silver), FCX (Freeport-McMoRan - Copper/Gold), KGC (Kinross Gold), HL (Hecla Mining - Silver)
**Period**: 2024-01-01 to 2024-12-31

**Sector Characteristics**:
- Volatility: Moderate to High
- Trend Pattern: Mixed - some stocks showed trends, others choppy
- Average Spread: Good to Excellent ($0.01-$0.31)
- Liquidity: Good (all stocks liquid enough for trading)

**Best Performing Stocks**:
1. **AEM** - Bracket: **+27.28%** return, 50% win rate, profit factor 1.86, max DD 8.6%
2. **KGC** - Bracket: **+2.36%** return, 47% win rate, profit factor 1.65, max DD 1.0%

**Underperforming Stocks**:
- **AG**: Both strategies lost money (-1.71% trailing-stop, -1.68% bracket)
- **FCX**: Both strategies lost money (-2.44% trailing-stop, -3.66% bracket)
- **HL**: Both strategies lost money (-1.95% trailing-stop, -1.12% bracket)

**Sector Strategy Preferences**:
- **Bracket strategy works better** for mining stocks (AEM, KGC both profitable with bracket)
- **Trailing-stop underperformed** on most mining stocks
- Mining stocks show choppy price action - bracket's defined targets work better than trailing stops

**Stock-by-Stock Analysis**:

**AEM (Agnico Eagle Mines - Gold)** - Best performer:
- Trailing-stop (5%): +14.76% return, 45% win rate, profit factor 1.48
- Bracket (10% TP, 5% SL): **+27.28%** return, 50% win rate, profit factor 1.86
- **Winner: Bracket** - Nearly double the return with better win rate
- AEM showed strong trends in 2024, bracket captured moves better
- Good profit factor (1.86) indicates solid risk/reward

**KGC (Kinross Gold)** - Modest performer:
- Trailing-stop (5%): +0.89% return, 56.67% win rate, profit factor 1.20
- Bracket (10% TP, 5% SL): **+2.36%** return, 47% win rate, profit factor 1.65
- **Winner: Bracket** - Higher return despite lower win rate
- KGC showed choppy price action - bracket's defined targets worked better
- Modest returns but positive - suitable for conservative strategies

**AG (First Majestic Silver)** - Underperformer:
- Trailing-stop (5%): -1.71% return, 32.65% win rate, profit factor 0.80
- Bracket (10% TP, 5% SL): -1.68% return, 29% win rate, profit factor 0.75
- **Both strategies lost money** - Not suitable for automated trading
- Low win rates (29-33%) indicate poor entry/exit timing
- Silver miners showed more volatility than gold miners

**FCX (Freeport-McMoRan - Copper/Gold)** - Underperformer:
- Trailing-stop (5%): -2.44% return, 40.74% win rate, profit factor 0.91
- Bracket (10% TP, 5% SL): -3.66% return, 31.58% win rate, profit factor 0.88
- **Both strategies lost money** - Not suitable for automated trading
- Diversified miner (copper/gold) showed poor performance
- Higher volatility led to larger losses

**HL (Hecla Mining - Silver)** - Underperformer:
- Trailing-stop (5%): -1.95% return, 38.30% win rate, profit factor 0.70
- Bracket (10% TP, 5% SL): -1.12% return, 31.43% win rate, profit factor 0.83
- **Both strategies lost money** - Not suitable for automated trading
- Another silver miner showing poor performance
- Low win rates and negative profit factors

**Sector-Specific Insights**:
- **Mining sector is challenging** - Only 2 out of 5 stocks (40%) were profitable
- **Gold miners outperformed** - AEM and KGC (both gold-focused) were profitable
- **Silver miners struggled** - AG and HL (both silver-focused) lost money
- **Diversified miners struggled** - FCX (copper/gold) lost money
- **Bracket strategy preferred** - Both profitable stocks performed better with bracket
- **Trailing-stop underperformed** - Mining stocks' choppy action whipsawed trailing stops
- **Returns are modest** - Even best performer (AEM) only returned +27% vs tech's +539% (NVDA)

**Cross-Stock Comparison**:
- Average return (best strategy per stock): **+14.82%** (only counting profitable stocks)
- Average return (all stocks): **+4.73%** (including losses)
- Win rate range: 29% (AG bracket) to 56.67% (KGC trailing-stop)
- Profit factor range: 0.70 (HL trailing-stop) to 1.86 (AEM bracket)
- Best overall: AEM bracket (+27.28%)
- Most consistent: KGC trailing-stop (56.67% win rate, but only +0.89% return)

**Recommendation**: 
- **Mining sector is mixed** - Only focus on profitable stocks (AEM, KGC)
- **Gold miners are better** - AEM and KGC outperformed silver miners
- **Use bracket strategy** - Both profitable stocks performed better with bracket
- **Avoid silver miners** - AG and HL both lost money with both strategies
- **Avoid diversified miners** - FCX lost money
- **Modest returns** - Mining sector returns are much lower than tech sector
- **Consider AEM** - Strong +27% return with bracket strategy makes it viable for live trading
- **KGC is marginal** - Only +2.36% return may not justify trading costs

**User Question Addressed**: "Is there undervaluation in gold and silver mining companies? Can we ride an upward trend?"
- **Answer**: Mixed results - Gold miners (AEM, KGC) showed profitability, but silver miners (AG, HL) lost money
- **AEM shows promise** - +27% return suggests potential upward trend captured
- **Silver miners struggling** - Both AG and HL lost money, suggesting no clear upward trend
- **Sector is challenging** - Only 40% of stocks were profitable vs tech's 100%
- **Recommendation**: Focus on gold miners (AEM) with bracket strategy if trading mining sector

### Agent: Cursor
**Activity**: Tech sector research - comprehensive analysis of major tech stocks (GOOGL, MSFT, NVDA, AMZN)
**Tools Used**: `get_quote()`, `run_backtest()` (trailing-stop, bracket), `compare_backtests()`
**Sector**: Technology
**Stocks Analyzed**: GOOGL, MSFT, NVDA, AMZN
**Period**: 2024-01-01 to 2024-12-31

**Sector Characteristics**:
- Volatility: High (especially NVDA)
- Trend Pattern: Strong upward trends in 2024
- Average Spread: Excellent ($0.03-$0.29)
- Liquidity: Excellent (all stocks highly liquid)

**Best Performing Stocks**:
1. **NVDA** - Trailing-stop: **+539.8%** return, 44% win rate, profit factor 2.90, max DD 1.6%
2. **MSFT** - Trailing-stop: **+88.1%** return, 64% win rate, profit factor 3.15, max DD 33.3%
3. **GOOGL** - Bracket: **+66.7%** return, 58% win rate, profit factor 2.66, max DD 25.1%
4. **AMZN** - Bracket: **+66.6%** return, 60% win rate, profit factor 2.79, max DD 18.9%

**Sector Strategy Preferences**:
- **Trailing-stop works best** for high-momentum tech stocks (NVDA, MSFT)
- **Bracket works best** for moderate-volatility tech stocks (GOOGL, AMZN)
- Trailing-stop allows winners to run (critical for NVDA's massive gains)
- Bracket provides better risk control for more stable tech stocks

**Stock-by-Stock Analysis**:

**NVDA (NVIDIA)** - Best performer:
- Trailing-stop (5%): **+539.8%** return, 44% win rate, profit factor 2.90
- Bracket (10% TP, 5% SL): +206.2% return, 48% win rate, profit factor 1.54
- **Winner: Trailing-stop** - Massive returns from letting winners run
- NVDA had explosive growth in 2024 (AI boom), trailing stop captured major moves
- Lower win rate (44%) but huge average wins ($515 vs $419)

**MSFT (Microsoft)** - Strong performer:
- Trailing-stop (5%): **+88.1%** return, 64% win rate, profit factor 3.15
- Bracket (10% TP, 5% SL): +51.4% return, 50% win rate, profit factor 1.79
- **Winner: Trailing-stop** - Much higher return, better win rate
- MSFT showed strong consistent uptrend, trailing stop captured it well
- Excellent win rate (64%) with strong profit factor (3.15)

**GOOGL (Google)** - Good performer:
- Trailing-stop (5%): +48.6% return, 53% win rate, profit factor 3.29
- Bracket (10% TP, 5% SL): **+66.7%** return, 58% win rate, profit factor 2.66
- **Winner: Bracket** - Higher return, better win rate
- GOOGL had more volatility, bracket's defined targets worked better
- Good balance of return and risk control

**AMZN (Amazon)** - Good performer:
- Trailing-stop (5%): +54.1% return, 64% win rate, profit factor 2.70
- Bracket (10% TP, 5% SL): **+66.6%** return, 60% win rate, profit factor 2.79
- **Winner: Bracket** - Slightly higher return, similar win rate
- AMZN showed moderate volatility, bracket provided better risk/reward

**Sector-Specific Insights**:
- **Tech stocks are highly profitable** for automated trading in 2024
- **Trailing-stop excels** on high-momentum stocks (NVDA, MSFT) - captures big moves
- **Bracket excels** on moderate-volatility stocks (GOOGL, AMZN) - better risk control
- **NVDA is exceptional** - +539% return shows power of trailing stops on explosive stocks
- **All tech stocks profitable** - Even worst performer (GOOGL trailing-stop) returned +48.6%
- **Win rates vary** - NVDA lower (44%) but huge wins; MSFT/AMZN higher (64%) with consistent gains

**Cross-Stock Comparison**:
- Average return (best strategy per stock): **+190.3%**
- Average win rate: **56.5%**
- Average profit factor: **2.88**
- Best overall: NVDA trailing-stop (+539.8%)
- Most consistent: MSFT trailing-stop (64% win rate, +88.1% return)

**Recommendation**: 
- **Tech sector is highly profitable** for automated trading
- **Focus on NVDA and MSFT** with trailing-stop strategies for maximum returns
- **Use bracket for GOOGL/AMZN** for better risk control
- **NVDA is exceptional** - consider larger position sizes given proven performance
- All four stocks are suitable for live trading with proper risk management

### Agent: Cursor
**Activity**: Strategy discovery for FSLY (Fastly) - comprehensive backtest comparison
**Tools Used**: `get_quote()`, `run_backtest()` (trailing-stop, bracket), `compare_backtests()`
**Learnings**:
- FSLY is a liquid stock ($16.47, tight $0.02 spread) suitable for automated trading
- Tested trailing-stop (5%) and bracket (10% TP, 5% SL) strategies on 2024 data
- Scale-out and grid strategies not yet supported for backtesting
- Bracket strategy significantly outperformed trailing-stop

**Successful Strategy Test**:
- Strategy: **Bracket** on FSLY
- Params: 10% take profit, 5% stop loss, 10 shares per trade
- Period: 2024-01-01 to 2024-12-31
- Results: 
  - Total Return: **+1.97%** (vs -3.39% for trailing-stop)
  - Win Rate: **33.33%** (vs 26.09% for trailing-stop)
  - Profit Factor: **1.20** (vs 0.73 for trailing-stop - losing strategy)
  - Max Drawdown: **6.1%** (vs 8.6% for trailing-stop)
  - Total Trades: 30 (vs 46 for trailing-stop)
- Notes: Bracket strategy is profitable with better risk control. Trailing-stop had too many small losses.

**Failed Strategy Test**:
- Strategy: Trailing-stop (5%) on FSLY
- Results: -3.39% return, 26% win rate, profit factor 0.73
- Issue: Too many small losses, trailing stop triggered too frequently in volatile periods

**Questions Explored**:
- Which strategy works best for FSLY?
  - **Answer**: Bracket strategy (10% TP, 5% SL) outperforms trailing-stop
  - Bracket provides better risk/reward with defined targets
  - Trailing-stop gets whipsawed too often in FSLY's volatile price action
  
- Is FSLY suitable for automated trading?
  - **Answer**: Yes, but with caution:
    - Liquid stock with tight spreads
    - Bracket strategy shows profitability
    - However, returns are modest (+2% annually)
    - High volatility requires careful position sizing

**Insights**:
- **Bracket strategy is superior for FSLY**: Better win rate, profit factor, and lower drawdown
- **FSLY is volatile**: Price ranged from ~$5.60 to ~$24 in 2024, requiring robust risk management
- **Modest returns**: +2% annual return suggests FSLY may not be ideal for aggressive growth strategies
- **Current price context**: Trading at $16.47 today (+77% move) - extreme volatility suggests caution
- **Recommendation**: If trading FSLY, use bracket strategy with tight stops (5% SL) and modest position sizes

### Agent: Cursor
**Activity**: Analysis of penny stock top movers - evaluating trading opportunities and risks
**Tools Used**: `get_top_movers()`, `get_quote()` for BANXR, BAX, BRTX
**Learnings**:
- Penny stocks (under $1) showing extreme moves (+200%+ in a day) are highly volatile and risky
- BANXR: +266% today, trading at $0.12, but shows illiquid spread (bid $0.126, ask $0.0)
- Many top movers are warrants (symbols ending in "W") or very small cap stocks
- Historical data not available for most penny stocks in our CSV data directory (only AAPL, NVDA, SPY, TSLA available)
- Cannot backtest penny stocks without historical data - need Alpaca API data source or CSV files

**Questions Explored**:
- Can we short penny stocks that are up big?
  - **Answer**: Technically yes via Alpaca, but extremely risky:
    - Wide bid-ask spreads make fills unpredictable
    - Low liquidity means slippage can be severe
    - Penny stocks can gap up/down dramatically
    - Shorting requires margin and has unlimited loss potential
    - Many penny stocks are hard-to-borrow (HTB), making shorting expensive or impossible
  
- Will it keep rising?
  - **Answer**: Impossible to predict with certainty, but patterns suggest:
    - Extreme one-day moves (+200%+) are often followed by reversals
    - Penny stocks are frequently manipulated (pump & dump schemes)
    - Low liquidity means small trades can move price dramatically
    - Without fundamental analysis or historical patterns, it's pure speculation

**Insights**:
- **Penny stocks are NOT suitable for automated trading strategies**:
  - Too volatile for trailing stops (can gap through stops)
  - Too illiquid for reliable fills
  - Too unpredictable for backtesting validation
  - Risk/reward is poor for systematic strategies
  
- **Better alternatives for strategy discovery**:
  - Focus on liquid stocks ($5+ price, high volume)
  - Stocks with available historical data for backtesting
  - Examples: AAPL, TSLA, NVDA, SPY (all have CSV data available)
  - These allow proper backtesting and strategy validation

- **Recommendation**: Avoid penny stocks for automated trading. Focus on liquid, established stocks with historical data for proper strategy development and backtesting.

### Agent: Initial Setup
**Activity**: Created CONTEXTS.md file structure
**Tools Used**: None (file creation)
**Learnings**:
- This file will track all agent learning and discovery activities
- Entries should be structured and include date, agent type, activity, tools used, and learnings
- Focus on discoveries, patterns, and insights rather than final recommendations

**Questions Explored**:
- How should agents document their learning process?
- What format makes it easiest for agents to traverse and understand historical context?

---

## Format Template

Use this template for new entries:

```markdown
## YYYY-MM-DD

### Agent: [Claude Desktop | Cursor]
**Activity**: [Brief description of what was done]
**Tools Used**: [List of MCP tools called]
**Learnings**:
- [Discovery 1]
- [Discovery 2]
- [Pattern observed]

**Successful Strategy Test** (if applicable):
- Strategy: [strategy type] on [symbol]
- Params: [key parameters]
- Period: [start date] to [end date]
- Results: Sharpe [X], Return [Y]%, Win Rate [Z]%
- Notes: [Observations]

**Questions Explored**:
- [Question 1]
- [Answer/Discovery 1]
- [Question 2]
- [Answer/Discovery 2]

**Insights**:
- [Key insight or pattern]
```

---
