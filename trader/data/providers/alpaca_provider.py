"""Alpaca API data provider for historical market data."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

import pandas as pd
import pytz
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame
from alpaca.data.timeframe import TimeFrameUnit

from trader.data.providers.base import DataProvider, TimeFrame
from trader.utils.logging import get_logger

_EASTERN_TZ = pytz.timezone("US/Eastern")


class AlpacaDataProvider(DataProvider):
    """Fetch historical OHLCV data from Alpaca."""

    def __init__(self, api_key: str, secret_key: str, feed: str | None = None) -> None:
        if not api_key or not secret_key:
            raise ValueError("Alpaca API credentials are required for data provider")
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.feed = feed
        self.logger = get_logger("autotrader.data.alpaca")

    def get_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        if not symbols:
            raise ValueError("symbols list cannot be empty")
        if start > end:
            raise ValueError("start date must be <= end date")

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            start=start,
            end=end,
            timeframe=_to_alpaca_timeframe(timeframe),
            feed=self.feed,
        )

        response = self.client.get_stock_bars(request)
        df = response.df

        if df is None or df.empty:
            raise ValueError("No data returned from Alpaca for requested symbols/date range")

        result = _split_bars(df, symbols)
        missing = [symbol for symbol in symbols if symbol not in result]
        if missing:
            raise ValueError(f"No Alpaca data returned for symbols: {', '.join(missing)}")

        for symbol, bars in result.items():
            result[symbol] = _normalize_bars(bars, symbol)

        return result


def _to_alpaca_timeframe(timeframe: TimeFrame) -> AlpacaTimeFrame:
    if timeframe == TimeFrame.DAY_1:
        return AlpacaTimeFrame.Day
    if timeframe == TimeFrame.HOUR_1:
        return AlpacaTimeFrame.Hour
    if timeframe == TimeFrame.MIN_15:
        return AlpacaTimeFrame(15, TimeFrameUnit.Minute)
    if timeframe == TimeFrame.MIN_5:
        return AlpacaTimeFrame(5, TimeFrameUnit.Minute)
    if timeframe == TimeFrame.MIN_1:
        return AlpacaTimeFrame.Minute
    raise ValueError(f"Unsupported timeframe: {timeframe.value}")


def _split_bars(df: pd.DataFrame, symbols: Iterable[str]) -> dict[str, pd.DataFrame]:
    if "symbol" in df.index.names:
        reset = df.reset_index()
        result: dict[str, pd.DataFrame] = {}
        for symbol, group in reset.groupby("symbol"):
            group = group.drop(columns=["symbol"])
            group = group.set_index("timestamp")
            result[symbol] = group
        return result

    symbol_list = list(symbols)
    if len(symbol_list) != 1:
        raise ValueError("Unexpected Alpaca response format for multi-symbol request")
    return {symbol_list[0]: df}


def _normalize_bars(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")

    df = df.rename(columns=str.lower)

    required = ["open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Alpaca data for {symbol} missing columns: {missing}")

    df = df[required].copy()
    df = df.sort_index()

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(_EASTERN_TZ)
    else:
        df.index = df.index.tz_convert(_EASTERN_TZ)

    df = df.astype("float64")

    if df.isnull().any().any():
        raise ValueError(f"Alpaca data for {symbol} contains NaN values")

    return df
