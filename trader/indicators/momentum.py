"""Momentum indicators."""

from __future__ import annotations

import pandas as pd

from baretrader.indicators.base import Indicator, IndicatorSpec, validate_ohlcv
from baretrader.indicators.ta_integration import get_pandas_ta


class RSI(Indicator):
    """Relative Strength Index."""

    def __init__(self, period: int = 14) -> None:
        self.period = period

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="rsi",
            description="Relative Strength Index",
            params={"period": "Lookback period (default: 14)"},
            output="Series named rsi_{period}",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("close",))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.rsi(data["close"], length=self.period)
            if series is None:
                raise ValueError("Failed to compute RSI")
        else:
            delta = data["close"].diff()
            gain = delta.clip(lower=0).rolling(self.period).mean()
            loss = (-delta.clip(upper=0)).rolling(self.period).mean()
            rs = gain / loss
            series = 100 - (100 / (1 + rs))
        series.name = f"rsi_{self.period}"
        return series


class MACD(Indicator):
    """Moving Average Convergence Divergence."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="macd",
            description="MACD (fast/slow EMA difference with signal)",
            params={
                "fast": "Fast EMA period (default: 12)",
                "slow": "Slow EMA period (default: 26)",
                "signal": "Signal EMA period (default: 9)",
            },
            output="DataFrame with MACD, signal, histogram columns",
        )

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        validate_ohlcv(data, ("close",))
        ta = get_pandas_ta()
        if ta is not None:
            df = ta.macd(
                data["close"], fast=self.fast, slow=self.slow, signal=self.signal
            )
            if df is None:
                raise ValueError("Failed to compute MACD")
            return df

        ema_fast = data["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = data["close"].ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return pd.DataFrame(
            {
                "MACD": macd_line,
                "SIGNAL": signal_line,
                "HISTOGRAM": histogram,
            },
            index=data.index,
        )
