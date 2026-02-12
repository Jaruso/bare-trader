# Timing Indicators for Strategy Entry/Exit

This document tracks indicators and market conditions that signal optimal entry/exit timing for both bullish and bearish strategies.

## Purpose

Identify market conditions, technical indicators, and data patterns that indicate:
- **When to enter** a strategy (bullish or bearish)
- **When to avoid** entering (wait for better conditions)
- **When to exit** early (before stop-loss/take-profit)

## Indicator Categories

### 1. Market Regime Indicators
- **VIX Level**: Volatility index (high = fear, low = complacency)
- **Market Trend**: SPY/QQQ direction (uptrend/downtrend/sideways)
- **Sector Rotation**: Which sectors are leading/lagging
- **Market Breadth**: Advance/decline ratio

### 2. Technical Indicators
- **RSI (14)**: Overbought (>70) / Oversold (<30)
- **MACD**: Bullish/bearish crossover signals
- **Bollinger Bands**: Price near upper/lower bands
- **Moving Averages**: Price vs SMA/EMA (20, 50, 200)
- **ATR**: Volatility levels (high/low)

### 3. Entry/Exit Timing Signals
- **Entry Conditions**: What market state favors entry
- **Exit Conditions**: Early exit signals before stops
- **Avoid Conditions**: When NOT to enter

## Strategy-Specific Timing

### Bearish Strategies (Inverse ETFs)

#### SQQQ (3x Inverse Nasdaq)
**Backtest Results** (2024):
- Trailing-stop: +13.25% return, 22.9% win rate, 48 trades
- Bracket: +1.03% return, 30.3% win rate, 33 trades

**Timing Indicators to Track**:
- [ ] Nasdaq-100 (QQQ) RSI > 70 (overbought) = good entry
- [ ] QQQ price above upper Bollinger Band = entry signal
- [ ] Tech sector weakness / rotation out of tech
- [ ] VIX spike (>20) = favorable for inverse ETFs
- [ ] Market breadth deteriorating (more decliners than advancers)

**Entry Conditions**:
- Tech sector showing weakness
- QQQ making new highs but momentum slowing
- High volatility environment

**Exit Conditions**:
- QQQ showing strength / bounce
- VIX dropping rapidly
- Market breadth improving

#### SPXU (3x Inverse S&P 500)
**Backtest Results** (2024):
- Trailing-stop: +13.73% return, 31.25% win rate, 32 trades
- Bracket: -10.62% return, 18.2% win rate, 22 trades

**Timing Indicators to Track**:
- [ ] SPY RSI > 70 = entry signal
- [ ] SPY above upper Bollinger Band
- [ ] Broad market weakness
- [ ] Sector rotation to defensive stocks

**Entry Conditions**:
- Broad market showing weakness
- Multiple sectors declining
- High VIX

**Exit Conditions**:
- Market stabilization
- VIX dropping
- Sector rotation back to growth

#### SH (1x Inverse S&P 500)
**Backtest Results** (2024):
- Trailing-stop: +28.39% return, 42.9% win rate, 7 trades
- Bracket: -1.37% return, 20% win rate, 5 trades

**Timing Indicators to Track**:
- [ ] Lower volatility than SPXU (1x vs 3x)
- [ ] Better for longer holds
- [ ] SPY trend reversal signals

**Entry Conditions**:
- Moderate bearish view (less aggressive than SPXU)
- Can hold longer due to no leverage decay

**Exit Conditions**:
- Market showing strength
- Trend reversal confirmed

#### PSQ (1x Inverse QQQ)
**Backtest Results** (2024):
- Trailing-stop: +28.52% return, 25% win rate, 12 trades
- Bracket: -6.69% return, 22.2% win rate, 9 trades

**Timing Indicators to Track**:
- [ ] QQQ showing weakness
- [ ] Tech sector rotation
- [ ] Lower volatility than SQQQ

**Entry Conditions**:
- Tech sector weakness
- Moderate bearish view

**Exit Conditions**:
- Tech sector strength
- QQQ bounce

### Bullish Strategies

#### NVDA (Trailing-Stop)
**Backtest Results** (2024):
- +539.8% return, 44.4% win rate, 36 trades

**Timing Indicators to Track**:
- [ ] RSI < 30 (oversold) = good entry
- [ ] Price near lower Bollinger Band = entry
- [ ] MACD bullish crossover
- [ ] Price above key moving averages
- [ ] High volume on up days

**Entry Conditions**:
- Strong uptrend
- Momentum building
- Low volatility (allows trailing stop to work)

**Exit Conditions**:
- RSI > 70 (overbought)
- Price near upper Bollinger Band
- Volume drying up

#### MSFT (Trailing-Stop)
**Backtest Results** (2024):
- +88.1% return, 63.6% win rate, 11 trades

**Timing Indicators to Track**:
- [ ] RSI < 40 = entry
- [ ] Price above 200-day MA
- [ ] Consistent uptrend
- [ ] Lower volatility than NVDA

**Entry Conditions**:
- Stable uptrend
- Moderate volatility
- Above key support levels

**Exit Conditions**:
- Trend reversal
- High volatility spike
- Breaking key support

## Data Keys Available in Backtest JSON Files

### From Backtest JSON Structure:
```json
{
  "id": "backtest_id",
  "strategy_type": "trailing_stop" | "bracket",
  "symbol": "SYMBOL",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "trades": [
    {
      "id": "order_id",
      "timestamp": "YYYY-MM-DD HH:MM:SS",
      "symbol": "SYMBOL",
      "side": "buy" | "sell",
      "qty": "10",
      "price": "123.45",
      "total": "1234.50"
    }
  ],
  "equity_curve": [
    ["YYYY-MM-DD HH:MM:SS", "equity_value"],
    ...
  ]
}
```

### Key Data Points to Extract:
1. **Entry Timestamps**: `trades[].timestamp` where `side == "buy"`
2. **Exit Timestamps**: `trades[].timestamp` where `side == "sell"`
3. **Entry Prices**: `trades[].price` for buy orders
4. **Exit Prices**: `trades[].price` for sell orders
5. **P/L per Trade**: Calculate from buy/sell pairs
6. **Equity Curve**: Time series of portfolio value
7. **Trade Duration**: Time between entry and exit

### Indicators to Calculate at Entry/Exit Points:
1. **RSI (14)**: Overbought (>70) / Oversold (<30)
2. **MACD**: Bullish/bearish crossover, histogram direction
3. **Bollinger Bands**: Price position relative to bands
4. **SMA/EMA (20, 50, 200)**: Price vs moving averages
5. **ATR (14)**: Volatility level
6. **Volume**: High/low volume at entry/exit
7. **Price Change**: % change from previous day/week

### Market Context Indicators (External):
1. **VIX Level**: Volatility index (need to fetch)
2. **SPY/QQQ Trend**: Market direction (need to fetch)
3. **Sector Performance**: Relative strength (need to fetch)
4. **Market Breadth**: Advance/decline ratio (need to fetch)

## Analysis Framework

For each backtest result, extract:
- Entry date/time
- Entry price
- Exit date/time  
- Exit price
- P/L
- Market conditions at entry (if available)
- Market conditions at exit (if available)

Then analyze:
- What indicators were present at winning entries?
- What indicators were present at losing entries?
- What conditions led to early exits?
- What conditions led to best performance?

## Analysis Tools

### Script: `scripts/analyze_timing_indicators.py`

A Python script to analyze timing indicators from backtest results:

**Usage:**
```bash
python scripts/analyze_timing_indicators.py <backtest_id>
```

**What it does:**
1. Loads a backtest result by ID
2. Extracts matched buy/sell trade pairs
3. Calculates indicators at entry and exit points:
   - RSI (14)
   - MACD (signal, histogram)
   - Bollinger Bands (position relative to bands)
   - SMA (20, 50) vs price
   - ATR (volatility)
   - Volume ratio
   - Price change %
4. Compares indicators for winning vs losing trades
5. Outputs JSON with analysis results

**Example Output:**
```json
{
  "symbol": "SQQQ",
  "strategy_type": "trailing_stop",
  "total_trades": 48,
  "winning_trades": 11,
  "losing_trades": 37,
  "win_rate": 22.9,
  "entry_indicators": {
    "winner_rsi_avg": 65.2,
    "loser_rsi_avg": 58.4,
    "winner_bb_pos_avg": 0.72,
    "loser_bb_pos_avg": 0.45
  }
}
```

## Next Steps

1. ✅ Backtest inverse ETFs (SQQQ, SPXU, SH, PSQ)
2. ✅ Create timing indicator analysis script
3. ⏳ Run analysis on all bearish strategy backtests
4. ⏳ Extract timing data from backtest results
5. ⏳ Calculate indicators at entry/exit points
6. ⏳ Identify patterns in winning vs losing trades
7. ⏳ Document optimal entry/exit conditions
8. ⏳ Create timing signal checklist
9. ⏳ Apply same analysis to bullish strategies

---

## 2026-02-12 - Initial Bearish Strategy Backtests

### SQQQ Results Summary
- **Trailing-Stop (5%)**: +13.25% return, 22.9% win rate, 48 trades
  - Best trade: +$270.56 (Nov 2024)
  - Worst trade: -$23.38
  - Avg win: $28.56, Avg loss: -$4.91
  - Profit factor: 1.73
  - Max drawdown: -7.74%

- **Bracket (10% TP, 5% SL)**: +1.03% return, 30.3% win rate, 33 trades
  - Best trade: +$31.69
  - Worst trade: -$16.85
  - Avg win: $14.90, Avg loss: -$6.03
  - Profit factor: 1.07
  - Max drawdown: -5.24%

**Key Observation**: Trailing-stop significantly outperformed bracket for SQQQ. Low win rate (23%) but high profit factor (1.73) suggests trailing stops capture big moves.

### SPXU Results Summary
- **Trailing-Stop (5%)**: +13.73% return, 31.25% win rate, 32 trades
  - Best trade: +$278.73 (April 2024)
  - Worst trade: -$25.53
  - Avg win: $34.36, Avg loss: -$9.38
  - Profit factor: 1.67
  - Max drawdown: -11.93%

- **Bracket (10% TP, 5% SL)**: -10.62% return, 18.2% win rate, 22 trades
  - Best trade: +$34.86
  - Worst trade: -$18.00
  - Avg win: $23.63, Avg loss: -$11.15
  - Profit factor: 0.47
  - Max drawdown: -12.42%

**Key Observation**: Trailing-stop works much better than bracket for SPXU. Bracket strategy lost money (-10.62%).

### SH Results Summary
- **Trailing-Stop (5%)**: +28.39% return, 42.9% win rate, 7 trades
  - Best trade: +$301.41 (Sept 2024)
  - Worst trade: -$5.55
  - Avg win: $101.26, Avg loss: -$4.96
  - Profit factor: 15.30
  - Max drawdown: -1.74%

- **Bracket (10% TP, 5% SL)**: -1.37% return, 20% win rate, 5 trades
  - Best trade: +$10.77
  - Worst trade: -$6.54
  - Avg win: $10.77, Avg loss: -$6.11
  - Profit factor: 0.44
  - Max drawdown: -2.44%

**Key Observation**: SH trailing-stop performed exceptionally well (+28.39%) with very high profit factor (15.30). Only 7 trades but huge wins. Bracket lost money.

### PSQ Results Summary
- **Trailing-Stop (5%)**: +28.52% return, 25% win rate, 12 trades
  - Best trade: +$359.08 (Feb 2024)
  - Worst trade: -$32.84
  - Avg win: $135.66, Avg loss: -$13.53
  - Profit factor: 3.34
  - Max drawdown: -6.91%

- **Bracket (10% TP, 5% SL)**: -6.69% return, 22.2% win rate, 9 trades
  - Best trade: +$39.07
  - Worst trade: -$22.25
  - Avg win: $23.89, Avg loss: -$16.39
  - Profit factor: 0.42
  - Max drawdown: -6.69%

**Key Observation**: PSQ trailing-stop performed very well (+28.52%) with good profit factor (3.34). Bracket lost money.

## Pattern Recognition

### Common Patterns Across Bearish Strategies:
1. **Trailing-stop consistently outperforms bracket** for inverse ETFs
2. **Low win rates** (20-30%) but **high profit factors** (1.5-15.0)
3. **Large average wins** vs small average losses
4. **Fewer trades** for 1x inverse ETFs (SH, PSQ) vs 3x (SQQQ, SPXU)
5. **Bracket strategies lost money** for all inverse ETFs tested

### Timing Observations:
- **Best performance periods**: 
  - SH: Sept 2024 (huge win +$301)
  - PSQ: Feb 2024 (huge win +$359)
  - SPXU: April 2024 (huge win +$279)
  - SQQQ: Nov 2024 (huge win +$271)

- **Need to analyze**: What market conditions existed during these big win periods?
