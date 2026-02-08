"""Trend indicators."""

from __future__ import annotations

import pandas as pd

from trader.indicators.base import Indicator, IndicatorSpec, validate_ohlcv
from trader.indicators.ta_integration import get_pandas_ta


class SMA(Indicator):
    """Simple Moving Average."""

    def __init__(self, period: int = 20) -> None:
        self.period = period

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="sma",
            description="Simple Moving Average",
            params={"period": "Lookback period (default: 20)"},
            output="Series named sma_{period}",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("close",))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.sma(data["close"], length=self.period)
            if series is None:
                raise ValueError("Failed to compute SMA")
        else:
            series = data["close"].rolling(self.period).mean()
        series.name = f"sma_{self.period}"
        return series


class EMA(Indicator):
    """Exponential Moving Average."""

    def __init__(self, period: int = 20) -> None:
        self.period = period

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="ema",
            description="Exponential Moving Average",
            params={"period": "Lookback period (default: 20)"},
            output="Series named ema_{period}",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("close",))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.ema(data["close"], length=self.period)
            if series is None:
                raise ValueError("Failed to compute EMA")
        else:
            series = data["close"].ewm(span=self.period, adjust=False).mean()
        series.name = f"ema_{self.period}"
        return series
