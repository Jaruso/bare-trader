"""Volume-based indicators."""

from __future__ import annotations

import pandas as pd

from baretrader.indicators.base import Indicator, IndicatorSpec, validate_ohlcv
from baretrader.indicators.ta_integration import get_pandas_ta


class OBV(Indicator):
    """On-Balance Volume."""

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="obv",
            description="On-Balance Volume",
            params={},
            output="Series named obv",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("close", "volume"))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.obv(close=data["close"], volume=data["volume"])
            if series is None:
                raise ValueError("Failed to compute OBV")
        else:
            delta = data["close"].diff().fillna(0)
            direction = delta.where(delta == 0, delta / delta.abs())
            series = (direction * data["volume"]).cumsum()
        series.name = "obv"
        return series


class VWAP(Indicator):
    """Volume Weighted Average Price."""

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="vwap",
            description="Volume Weighted Average Price",
            params={},
            output="Series named vwap",
        )

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        validate_ohlcv(data, ("high", "low", "close", "volume"))
        ta = get_pandas_ta()
        if ta is not None:
            series = ta.vwap(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                volume=data["volume"],
            )
            if series is None:
                raise ValueError("Failed to compute VWAP")
        else:
            typical_price = (data["high"] + data["low"] + data["close"]) / 3
            cumulative_vp = (typical_price * data["volume"]).cumsum()
            cumulative_vol = data["volume"].cumsum()
            series = cumulative_vp / cumulative_vol
        series.name = "vwap"
        return series
