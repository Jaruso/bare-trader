"""Historical data loading for backtesting."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


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
    data_dir: Optional[Path] = None,
) -> dict[str, pd.DataFrame]:
    """Load historical data for backtesting.

    Args:
        symbols: List of stock symbols to load.
        start_date: Start date for data range.
        end_date: End date for data range.
        data_source: Data source ("csv" or "alpaca").
        data_dir: Directory containing CSV files (required for csv source).

    Returns:
        Dictionary mapping symbol to OHLCV DataFrame.

    Raises:
        ValueError: If data_source is invalid or required parameters missing.
        FileNotFoundError: If CSV file not found for a symbol.
    """
    if data_source == "csv":
        return _load_from_csv(symbols, start_date, end_date, data_dir)
    elif data_source == "alpaca":
        raise NotImplementedError("Alpaca data source coming in Phase 4")
    else:
        raise ValueError(f"Unknown data source: {data_source}")


def _load_from_csv(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    data_dir: Optional[Path] = None,
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

    result = {}

    for symbol in symbols:
        csv_file = data_dir / f"{symbol}.csv"
        if not csv_file.exists():
            raise FileNotFoundError(
                f"CSV file not found for {symbol}: {csv_file}. "
                f"Expected format: {data_dir}/{symbol}.csv"
            )

        # Load full CSV
        df = load_csv_data(csv_file)

        # Filter to date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        if len(df) == 0:
            raise ValueError(
                f"No data found for {symbol} in date range "
                f"{start_date.date()} to {end_date.date()}"
            )

        result[symbol] = df

    return result
