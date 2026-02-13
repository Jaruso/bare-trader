"""Visualization helpers for AutoTrader."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from trader.backtest.data import load_data_for_backtest
from trader.backtest.results import BacktestResult
from trader.data import TimeFrame
from trader.utils.logging import get_logger
from trader.visualization.chart import ChartBuilder

logger = get_logger("autotrader.visualization")


def default_historical_data_dir() -> Path:
    """Default directory for historical CSV data."""
    return Path.cwd() / "data" / "historical"


def load_price_data(
    result: BacktestResult,
    data_source: str = "csv",
    data_dir: Path | None = None,
    timeframe: TimeFrame = TimeFrame.DAY_1,
) -> pd.DataFrame | None:
    """Load OHLCV data for a backtest result.

    Returns None if data cannot be loaded.
    """
    if data_dir is None:
        data_dir = default_historical_data_dir()

    try:
        data = load_data_for_backtest(
            symbols=[result.symbol],
            start_date=result.start_date,
            end_date=result.end_date,
            data_source=data_source,
            data_dir=data_dir,
            timeframe=timeframe,
        )
    except Exception as exc:
        logger.warning(f"Unable to load price data for visualization: {exc}")
        return None

    return data.get(result.symbol)


def build_backtest_chart(
    result: BacktestResult,
    data_source: str = "csv",
    data_dir: Path | None = None,
    theme: str = "dark",
    include_price: bool = True,
) -> ChartBuilder:
    """Create a chart builder for a backtest result."""
    price_data = None
    if include_price:
        price_data = load_price_data(result, data_source=data_source, data_dir=data_dir)
        if price_data is None:
            logger.warning("Price data unavailable, rendering equity-only chart")

    return ChartBuilder(result=result, price_data=price_data, theme=theme)


__all__ = [
    "ChartBuilder",
    "build_backtest_chart",
    "load_price_data",
    "default_historical_data_dir",
]
