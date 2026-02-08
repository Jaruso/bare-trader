"""Factory for data providers."""

from __future__ import annotations

from pathlib import Path

from trader.data.providers.alpaca_provider import AlpacaDataProvider
from trader.data.providers.base import DataProvider
from trader.data.providers.cached_provider import CachedDataProvider
from trader.data.providers.csv_provider import CSVDataProvider
from trader.utils.config import Config


def get_data_provider(
    config: Config,
    source_override: str | None = None,
    historical_dir_override: Path | None = None,
    cache_override: bool | None = None,
) -> DataProvider:
    source = (source_override or config.data.source).lower()

    if source == "cached":
        base_source = config.data.source.lower()
        if base_source == "cached":
            base_source = "csv"
        base = _build_provider(config, base_source, historical_dir_override)
        cache_enabled = True
    else:
        base = _build_provider(config, source, historical_dir_override)
        cache_enabled = config.data.cache.enabled if cache_override is None else cache_override

    if cache_enabled:
        if config.data.cache.backend.lower() != "parquet":
            raise ValueError(
                f"Unsupported cache backend: {config.data.cache.backend}. Use 'parquet'."
            )
        return CachedDataProvider(
            base,
            cache_dir=config.data.cache.directory,
            ttl_minutes=config.data.cache.ttl_minutes,
        )

    return base


def _build_provider(
    config: Config,
    source: str,
    historical_dir_override: Path | None,
) -> DataProvider:
    if source == "csv":
        data_dir = historical_dir_override or config.data.csv_dir
        return CSVDataProvider(data_dir=data_dir)
    if source == "alpaca":
        return AlpacaDataProvider(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            feed=config.data.alpaca_feed,
        )
    raise ValueError(f"Unknown data source: {source}")
