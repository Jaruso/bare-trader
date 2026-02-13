"""CSV file data provider for historical market data."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz

from trader.data.providers.base import DataProvider, TimeFrame
from trader.utils.logging import get_logger

_EASTERN_TZ = pytz.timezone("US/Eastern")


class CSVDataProvider(DataProvider):
    """Load historical OHLCV data from CSV files.

    Expected file structure:
        {data_dir}/{SYMBOL}.csv

    Expected CSV format:
        timestamp,open,high,low,close,volume
        2024-01-01 09:30:00,175.00,176.50,174.80,176.20,1500000
        2024-01-02 09:30:00,176.20,177.00,175.50,176.80,1200000

    Currently supports daily bars only (1Day timeframe).
    """

    def __init__(self, data_dir: Path):
        """Initialize CSV data provider.

        Args:
            data_dir: Directory containing CSV files (e.g., "data/historical").
        """
        self.data_dir = Path(data_dir)
        self.logger = get_logger("autotrader.data.csv")

    def get_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        """Fetch historical OHLCV bars from CSV files.

        Args:
            symbols: List of stock symbols to load.
            start: Start datetime (inclusive).
            end: End datetime (inclusive).
            timeframe: Bar timeframe (default: 1Day).

        Returns:
            Dictionary mapping symbol to OHLCV DataFrame.

        Raises:
            ValueError: If timeframe not supported or invalid parameters.
            FileNotFoundError: If data directory or CSV file not found.
        """
        # Validate timeframe
        if timeframe != TimeFrame.DAY_1:
            raise ValueError(
                f"CSV provider only supports daily bars (1Day), got {timeframe.value}. "
                "For intraday data, use Alpaca provider or create intraday CSV files."
            )

        # Validate directory
        if not self.data_dir.exists():
            default_dir = Path.home() / ".autotrader" / "data" / "historical"
            suggestion = (
                f"Set HISTORICAL_DATA_DIR environment variable or create {self.data_dir}. "
                f"Default location: {default_dir}. "
                f"See README.md 'Backtesting with CSV Data' section for setup instructions."
            )
            raise FileNotFoundError(
                f"Data directory not found: {self.data_dir}. {suggestion}"
            )

        # Load data for each symbol
        result = {}
        for symbol in symbols:
            csv_file = self.data_dir / f"{symbol}.csv"

            # Load and filter CSV
            self.logger.debug(f"Loading {symbol} from {csv_file}")
            df = self._load_file(csv_file)
            df = df[(df.index >= start) & (df.index <= end)]

            if df.empty:
                raise ValueError(
                    f"No data found for {symbol} in date range "
                    f"{start.date()} to {end.date()}. "
                    f"Check that {csv_file} contains data in this range."
                )

            self.logger.info(f"Loaded {len(df)} bars for {symbol}")
            result[symbol] = df

        return result

    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """Load and validate a single CSV file.

        Args:
            file_path: Path to CSV file.

        Returns:
            DataFrame with DatetimeIndex and OHLCV columns.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If CSV format is invalid.
        """
        if not file_path.exists():
            default_dir = Path.home() / ".autotrader" / "data" / "historical"
            suggestion = (
                f"Expected format: {self.data_dir}/{{SYMBOL}}.csv. "
                f"Set HISTORICAL_DATA_DIR environment variable or create CSV files. "
                f"Default location: {default_dir}. "
                f"See README.md 'Backtesting with CSV Data' section for setup instructions."
            )
            raise FileNotFoundError(
                f"CSV file not found: {file_path}. {suggestion}"
            )

        try:
            df = pd.read_csv(file_path, parse_dates=["timestamp"])
        except Exception as e:
            raise ValueError(f"Failed to read CSV file {file_path}: {e}")

        # Validate required columns
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"CSV {file_path.name} missing required columns: {missing_columns}. "
                f"Expected columns: {required_columns}"
            )

        # Set timestamp as index
        df = df.set_index("timestamp")

        # Ensure timezone-aware index (US/Eastern preferred)
        if df.index.tz is None:
            df.index = df.index.tz_localize(_EASTERN_TZ)
        else:
            df.index = df.index.tz_convert(_EASTERN_TZ)

        # Sort by timestamp
        df = df.sort_index()

        # Normalize column casing and dtype
        df = df.rename(columns=str.lower)
        df = df.astype("float64")

        # Validate data quality
        if df.isnull().any().any():
            raise ValueError(f"CSV {file_path.name} contains NaN values")

        if df.empty:
            raise ValueError(f"CSV {file_path.name} is empty")

        return df
