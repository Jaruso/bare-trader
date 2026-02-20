"""Custom indicator examples."""

from __future__ import annotations

import pandas as pd

from baretrader.indicators.base import Indicator, IndicatorSpec, validate_ohlcv


class RollingHighLow(Indicator):
    """Rolling high/low bands."""

    def __init__(self, period: int = 20) -> None:
        self.period = period

    @property
    def spec(self) -> IndicatorSpec:
        return IndicatorSpec(
            name="rolling_high_low",
            description="Rolling high/low bands",
            params={"period": "Lookback period (default: 20)"},
            output="DataFrame with rolling_high/rolling_low",
        )

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        validate_ohlcv(data, ("high", "low"))
        df = pd.DataFrame(index=data.index)
        df["rolling_high"] = data["high"].rolling(self.period).max()
        df["rolling_low"] = data["low"].rolling(self.period).min()
        return df
