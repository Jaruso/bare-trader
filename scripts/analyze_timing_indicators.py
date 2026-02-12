#!/usr/bin/env python3
"""Analyze timing indicators from backtest results.

Extracts entry/exit timestamps and calculates indicators to identify
optimal timing signals for strategy entry/exit.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trader.indicators import get_indicator
from trader.data.providers import get_data_provider
from trader.utils.config import Config


def load_backtest(backtest_id: str) -> dict[str, Any]:
    """Load a backtest result by ID."""
    backtests_dir = Path(__file__).parent.parent / "data" / "backtests"
    backtest_file = backtests_dir / f"{backtest_id}.json"
    
    if not backtest_file.exists():
        raise FileNotFoundError(f"Backtest {backtest_id} not found")
    
    with open(backtest_file) as f:
        return json.load(f)


def extract_trades(backtest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract matched buy/sell pairs from backtest trades."""
    trades = backtest.get("trades", [])
    buys = [t for t in trades if t["side"] == "buy"]
    sells = [t for t in trades if t["side"] == "sell"]
    
    matched_trades = []
    for i, buy in enumerate(buys):
        if i < len(sells):
            sell = sells[i]
            entry_time = datetime.fromisoformat(buy["timestamp"].replace("Z", "+00:00"))
            exit_time = datetime.fromisoformat(sell["timestamp"].replace("Z", "+00:00"))
            entry_price = Decimal(buy["price"])
            exit_price = Decimal(sell["price"])
            pnl = (exit_price - entry_price) * Decimal(buy["qty"])
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            
            matched_trades.append({
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "qty": int(buy["qty"]),
                "pnl": float(pnl),
                "pnl_pct": float(pnl_pct),
                "duration_days": (exit_time - entry_time).days,
                "is_win": pnl > 0,
            })
    
    return matched_trades


def calculate_indicators_at_date(
    symbol: str,
    date: datetime,
    data_provider: Any,
    lookback_days: int = 50,
) -> dict[str, Any]:
    """Calculate indicators at a specific date."""
    end_date = date
    start_date = date - pd.Timedelta(days=lookback_days)
    
    try:
        # Get historical data
        data = data_provider.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe="1Day",
        )
        
        if data is None or len(data) == 0:
            return {}
        
        # Ensure we have OHLCV columns
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in data.columns for col in required_cols):
            return {}
        
        # Calculate indicators
        indicators = {}
        
        # RSI
        try:
            rsi = get_indicator("rsi", period=14)
            rsi_values = rsi.calculate(data)
            if len(rsi_values) > 0:
                indicators["rsi"] = float(rsi_values.iloc[-1])
        except Exception:
            pass
        
        # MACD
        try:
            macd = get_indicator("macd")
            macd_values = macd.calculate(data)
            if len(macd_values) > 0:
                indicators["macd"] = float(macd_values["MACD"].iloc[-1])
                indicators["macd_signal"] = float(macd_values["SIGNAL"].iloc[-1])
                indicators["macd_histogram"] = float(macd_values["HISTOGRAM"].iloc[-1])
        except Exception:
            pass
        
        # Bollinger Bands
        try:
            bb = get_indicator("bbands", period=20, stddev=2.0)
            bb_values = bb.calculate(data)
            if len(bb_values) > 0:
                current_price = float(data["close"].iloc[-1])
                indicators["bb_upper"] = float(bb_values["BBU"].iloc[-1])
                indicators["bb_middle"] = float(bb_values["BBM"].iloc[-1])
                indicators["bb_lower"] = float(bb_values["BBL"].iloc[-1])
                indicators["bb_position"] = (current_price - indicators["bb_lower"]) / (
                    indicators["bb_upper"] - indicators["bb_lower"]
                ) if (indicators["bb_upper"] - indicators["bb_lower"]) > 0 else 0.5
        except Exception:
            pass
        
        # Moving Averages
        try:
            sma20 = get_indicator("sma", period=20)
            sma50 = get_indicator("sma", period=50)
            sma_values_20 = sma20.calculate(data)
            sma_values_50 = sma50.calculate(data)
            if len(sma_values_20) > 0 and len(sma_values_50) > 0:
                current_price = float(data["close"].iloc[-1])
                indicators["sma20"] = float(sma_values_20.iloc[-1])
                indicators["sma50"] = float(sma_values_50.iloc[-1])
                indicators["price_vs_sma20"] = (current_price - indicators["sma20"]) / indicators["sma20"] * 100
                indicators["price_vs_sma50"] = (current_price - indicators["sma50"]) / indicators["sma50"] * 100
        except Exception:
            pass
        
        # ATR
        try:
            atr = get_indicator("atr", period=14)
            atr_values = atr.calculate(data)
            if len(atr_values) > 0:
                indicators["atr"] = float(atr_values.iloc[-1])
                indicators["atr_pct"] = (indicators["atr"] / float(data["close"].iloc[-1])) * 100
        except Exception:
            pass
        
        # Volume
        if "volume" in data.columns:
            recent_volume = data["volume"].tail(20).mean()
            current_volume = float(data["volume"].iloc[-1])
            indicators["volume_ratio"] = current_volume / recent_volume if recent_volume > 0 else 1.0
        
        # Price change
        if len(data) >= 2:
            current_price = float(data["close"].iloc[-1])
            prev_price = float(data["close"].iloc[-2])
            indicators["price_change_pct"] = ((current_price - prev_price) / prev_price) * 100
        
        return indicators
    
    except Exception as e:
        print(f"Error calculating indicators for {symbol} at {date}: {e}")
        return {}


def analyze_backtest_timing(backtest_id: str) -> dict[str, Any]:
    """Analyze timing indicators for a backtest."""
    backtest = load_backtest(backtest_id)
    symbol = backtest["symbol"]
    
    # Extract matched trades
    matched_trades = extract_trades(backtest)
    
    if not matched_trades:
        return {"error": "No matched trades found"}
    
    # Get data provider
    config = Config()
    data_provider = get_data_provider(config.data_source, config=config)
    
    # Calculate indicators for each trade
    trade_analysis = []
    for trade in matched_trades:
        entry_indicators = calculate_indicators_at_date(
            symbol, trade["entry_time"], data_provider
        )
        exit_indicators = calculate_indicators_at_date(
            symbol, trade["exit_time"], data_provider
        )
        
        trade_analysis.append({
            **trade,
            "entry_indicators": entry_indicators,
            "exit_indicators": exit_indicators,
        })
    
    # Aggregate statistics
    winning_trades = [t for t in trade_analysis if t["is_win"]]
    losing_trades = [t for t in trade_analysis if not t["is_win"]]
    
    # Analyze entry indicators for winners vs losers
    winner_entry_rsi = [
        t["entry_indicators"].get("rsi")
        for t in winning_trades
        if "rsi" in t["entry_indicators"]
    ]
    loser_entry_rsi = [
        t["entry_indicators"].get("rsi")
        for t in losing_trades
        if "rsi" in t["entry_indicators"]
    ]
    
    winner_entry_bb_pos = [
        t["entry_indicators"].get("bb_position")
        for t in winning_trades
        if "bb_position" in t["entry_indicators"]
    ]
    loser_entry_bb_pos = [
        t["entry_indicators"].get("bb_position")
        for t in losing_trades
        if "bb_position" in t["entry_indicators"]
    ]
    
    return {
        "symbol": symbol,
        "strategy_type": backtest["strategy_type"],
        "total_trades": len(trade_analysis),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": len(winning_trades) / len(trade_analysis) * 100 if trade_analysis else 0,
        "avg_winner_pnl": sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
        "avg_loser_pnl": sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        "entry_indicators": {
            "winner_rsi_avg": sum(winner_entry_rsi) / len(winner_entry_rsi) if winner_entry_rsi else None,
            "loser_rsi_avg": sum(loser_entry_rsi) / len(loser_entry_rsi) if loser_entry_rsi else None,
            "winner_bb_pos_avg": sum(winner_entry_bb_pos) / len(winner_entry_bb_pos) if winner_entry_bb_pos else None,
            "loser_bb_pos_avg": sum(loser_entry_bb_pos) / len(loser_entry_bb_pos) if loser_entry_bb_pos else None,
        },
        "trades": trade_analysis[:10],  # First 10 trades for inspection
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_timing_indicators.py <backtest_id>")
        sys.exit(1)
    
    backtest_id = sys.argv[1]
    result = analyze_backtest_timing(backtest_id)
    print(json.dumps(result, indent=2, default=str))
