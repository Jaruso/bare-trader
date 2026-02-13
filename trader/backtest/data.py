"""Historical data loading for backtesting."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from trader.data import DataProvider, TimeFrame, get_data_provider
from trader.utils.config import Config, load_config


def load_csv_data(file_path: Path) -> pd.DataFrame:
    """Load OHLCV data from CSV file.

    Expected CSV format:
        timestamp,open,high,low,close,volume
        2024-01-01 09:30:00,175.00,176.50,174.80,176.20,1500000
        2024-01-02 09:30:00,176.20,177.00,175.50,176.80,1200000

    Args:
        file_path: Path to CSV file.

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume.
        Index is the timestamp.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If CSV format is invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    try:
        df = pd.read_csv(file_path, parse_dates=["timestamp"])
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")

    # Validate required columns
    required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {missing_columns}")

    # Set timestamp as index
    df = df.set_index("timestamp")

    # Sort by timestamp
    df = df.sort_index()

    # Validate data quality
    if df.isnull().any().any():
        raise ValueError("CSV contains NaN values")

    if len(df) == 0:
        raise ValueError("CSV file is empty")

    return df


def load_data_for_backtest(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    data_source: str = "csv",
    data_dir: Path | None = None,
    timeframe: TimeFrame = TimeFrame.DAY_1,
    provider: DataProvider | None = None,
    config: Config | None = None,
) -> dict[str, pd.DataFrame]:
    """Load historical data for backtesting.

    Args:
        symbols: List of stock symbols to load.
        start_date: Start date for data range.
        end_date: End date for data range.
        data_source: Data source ("csv", "alpaca", or "cached").
        data_dir: Directory containing CSV files (required for csv source).
        timeframe: Bar timeframe for historical data.
        provider: Optional pre-configured data provider (overrides data_source).
        config: Optional config for provider factory (defaults to load_config()).

    Returns:
        Dictionary mapping symbol to OHLCV DataFrame.

    Raises:
        ValueError: If data_source is invalid or required parameters missing.
        FileNotFoundError: If CSV file not found for a symbol.
    """
    if provider is None:
        if config is None:
            config = load_config()
        provider = get_data_provider(
            config=config,
            source_override=data_source,
            historical_dir_override=data_dir,
        )

    return provider.get_bars(symbols, start_date, end_date, timeframe=timeframe)


def _load_from_csv(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    data_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load data from CSV files.

    Expects files named: {SYMBOL}.csv in data_dir.
    Example: AAPL.csv, GOOGL.csv

    Args:
        symbols: List of symbols to load.
        start_date: Filter data >= this date.
        end_date: Filter data <= this date.
        data_dir: Directory containing CSV files.

    Returns:
        Dictionary mapping symbol to filtered DataFrame.

    Raises:
        ValueError: If data_dir not provided.
        FileNotFoundError: If CSV file not found for a symbol.
    """
    if data_dir is None:
        raise ValueError("data_dir is required for CSV data source")

    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    from trader.data.providers.csv_provider import CSVDataProvider

    provider = CSVDataProvider(data_dir=data_dir)
    return provider.get_bars(symbols, start_date, end_date, timeframe=TimeFrame.DAY_1)
