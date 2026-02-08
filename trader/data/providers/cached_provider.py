"""Cached data provider with Parquet storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from trader.data.providers.base import DataProvider, TimeFrame
from trader.utils.logging import get_logger


@dataclass(frozen=True)
class CacheKey:
    symbol: str
    start: datetime
    end: datetime
    timeframe: TimeFrame

    def filename(self) -> str:
        start_str = self.start.strftime("%Y%m%dT%H%M%S")
        end_str = self.end.strftime("%Y%m%dT%H%M%S")
        return f"{self.symbol}_{self.timeframe.value}_{start_str}_{end_str}.parquet"


class CachedDataProvider(DataProvider):
    """Wrap another data provider with Parquet caching."""

    def __init__(
        self,
        provider: DataProvider,
        cache_dir: Path,
        ttl_minutes: int = 60,
    ) -> None:
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.ttl_minutes = ttl_minutes
        self.logger = get_logger("autotrader.data.cache")

    def get_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        if not symbols:
            raise ValueError("symbols list cannot be empty")

        cached: dict[str, pd.DataFrame] = {}
        missing: list[str] = []

        for symbol in symbols:
            cache_path = self._cache_path(CacheKey(symbol, start, end, timeframe))
            if self._is_cache_valid(cache_path):
                cached[symbol] = _read_parquet(cache_path)
            else:
                missing.append(symbol)

        if missing:
            fetched = self.provider.get_bars(missing, start, end, timeframe)
            for symbol, df in fetched.items():
                cache_path = self._cache_path(CacheKey(symbol, start, end, timeframe))
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                _write_parquet(cache_path, df)
            cached.update(fetched)

        return cached

    def _cache_path(self, key: CacheKey) -> Path:
        safe_symbol = key.symbol.replace("/", "_")
        return self.cache_dir / safe_symbol / key.filename()

    def _is_cache_valid(self, path: Path) -> bool:
        if not path.exists():
            return False
        if self.ttl_minutes <= 0:
            return True
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - mtime).total_seconds()
        return age_seconds <= self.ttl_minutes * 60


def _read_parquet(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path)
    except ImportError as exc:
        raise ImportError(
            "Parquet caching requires pyarrow. Install with `pip install pyarrow`."
        ) from exc


def _write_parquet(path: Path, df: pd.DataFrame) -> None:
    try:
        df.to_parquet(path, index=True)
    except ImportError as exc:
        raise ImportError(
            "Parquet caching requires pyarrow. Install with `pip install pyarrow`."
        ) from exc
