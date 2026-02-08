"""Volatility indicators."""

from __future__ import annotations

import pandas as pd

from trader.indicators.base import Indicator, IndicatorSpec, validate_ohlcv
from trader.indicators.ta_integration import get_pandas_ta


class ATR(Indicator):
    """Average True Range."""

    def __init__(self, period: int = 14) -> None:
        self.period = period

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="atr",
            description="Average True Range",
            params={"period": "Lookback period (default: 14)"},
            output="Series named atr_{period}",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("high", "low", "close"))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.atr(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                length=self.period,
            )
            if series is None:
                raise ValueError("Failed to compute ATR")
        else:
            high_low = data["high"] - data["low"]
            high_close = (data["high"] - data["close"].shift()).abs()
            low_close = (data["low"] - data["close"].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            series = tr.rolling(self.period).mean()
        series.name = f"atr_{self.period}"
        return series


class BollingerBands(Indicator):
    """Bollinger Bands."""

    def __init__(self, period: int = 20, stddev: float = 2.0) -> None:
        self.period = period
        self.stddev = stddev

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="bbands",
            description="Bollinger Bands",
            params={
                "period": "Lookback period (default: 20)",
                "stddev": "Standard deviation multiplier (default: 2.0)",
            },
            output="DataFrame with lower/mid/upper bands",
        )

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        validate_ohlcv(data, ("close",))
        ta = get_pandas_ta()
        if ta is not None:
            df = ta.bbands(data["close"], length=self.period, std=self.stddev)
            if df is None:
                raise ValueError("Failed to compute Bollinger Bands")
            return df

        mid = data["close"].rolling(self.period).mean()
        std = data["close"].rolling(self.period).std()
        upper = mid + self.stddev * std
        lower = mid - self.stddev * std
        return pd.DataFrame(
            {
                "BBL": lower,
                "BBM": mid,
                "BBU": upper,
            },
            index=data.index,
        )
