"""Abstract base classes for data providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

import pandas as pd


class TimeFrame(str, Enum):
    """Supported timeframes for historical data.

    Values match Alpaca API naming convention for easy mapping.
    """

    DAY_1 = "1Day"
    HOUR_1 = "1Hour"
    MIN_15 = "15Min"
    MIN_5 = "5Min"
    MIN_1 = "1Min"


class DataProvider(ABC):
    """Abstract interface for historical data providers.

    All providers must return data in consistent format:
    - dict[str, pd.DataFrame] mapping symbol -> OHLCV data
    - DataFrame has DatetimeIndex (timezone-aware, US/Eastern preferred)
    - Columns: open, high, low, close, volume (lowercase)
    - Values are float64 (for pandas compatibility)
    - Sorted chronologically (earliest to latest)
    - No NaN values

    This interface allows pluggable data sources (CSV, Alpaca API, PostgreSQL, etc.)
    while maintaining consistent data format throughout the application.
    """

    @abstractmethod
    def get_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        """Fetch historical OHLCV bars for symbols.

        Args:
            symbols: List of stock symbols to fetch (e.g., ["AAPL", "GOOGL"]).
            start: Start datetime (inclusive).
            end: End datetime (inclusive).
            timeframe: Bar timeframe (default: 1Day).

        Returns:
            Dictionary mapping symbol to OHLCV DataFrame.

            Each DataFrame has:
            - Index: DatetimeIndex (timestamp)
            - Columns: open, high, low, close, volume
            - Sorted chronologically
            - No missing/NaN values

        Raises:
            ValueError: If invalid parameters (e.g., start > end, empty symbols).
            FileNotFoundError: If data not available (CSV provider).
            ConnectionError: If API unavailable (Alpaca provider).

        Example:
            >>> provider = CSVDataProvider("data/historical")
            >>> data = provider.get_bars(
            ...     symbols=["AAPL"],
            ...     start=datetime(2024, 1, 1),
            ...     end=datetime(2024, 12, 31),
            ...     timeframe=TimeFrame.DAY_1
            ... )
            >>> df = data["AAPL"]
            >>> print(df.columns)
            Index(['open', 'high', 'low', 'close', 'volume'], dtype='object')
        """
        pass
