"""Tests for indicator library."""

from datetime import datetime

import pandas as pd

from baretrader.indicators import get_indicator, list_indicators


def _sample_data() -> pd.DataFrame:
    index = pd.date_range(datetime(2024, 1, 1), periods=30, freq="D")
    return pd.DataFrame(
        {
            "open": [100 + i for i in range(30)],
            "high": [101 + i for i in range(30)],
            "low": [99 + i for i in range(30)],
            "close": [100.5 + i for i in range(30)],
            "volume": [1000000 for _ in range(30)],
        },
        index=index,
    )


def test_list_indicators() -> None:
    specs = list_indicators()
    names = {spec.name for spec in specs}
    assert "sma" in names
    assert "rsi" in names


def test_indicator_calculations() -> None:
    data = _sample_data()
    indicators = [
        ("sma", {"period": 5}),
        ("ema", {"period": 5}),
        ("rsi", {"period": 14}),
        ("macd", {"fast": 12, "slow": 26, "signal": 9}),
        ("atr", {"period": 14}),
        ("bbands", {"period": 20, "stddev": 2.0}),
        ("obv", {}),
        ("vwap", {}),
        ("rolling_high_low", {"period": 5}),
    ]

    for name, params in indicators:
        indicator_obj = get_indicator(name, **params)
        output = indicator_obj.calculate(data)
        assert output is not None
