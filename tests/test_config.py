"""Tests for configuration module."""

import os
from unittest.mock import patch

from trader.utils.config import (
    Config,
    Environment,
    Service,
    StrategyDefaults,
    load_config,
)


def test_environment_enum() -> None:
    """Test Environment enum values."""
    assert Environment.PAPER.value == "paper"
    assert Environment.PROD.value == "prod"


def test_service_enum() -> None:
    """Test Service enum values."""
    assert Service.ALPACA.value == "alpaca"


def test_config_is_paper() -> None:
    """Test is_paper property."""
    config = Config(
        env=Environment.PAPER,
        service=Service.ALPACA,
        base_url="https://paper-api.alpaca.markets",
        alpaca_api_key="test",
        alpaca_secret_key="test",
        data_dir=None,  # type: ignore
        log_dir=None,  # type: ignore
        strategy_defaults=StrategyDefaults(),
    )
    assert config.is_paper is True
    assert config.is_prod is False


def test_config_is_prod() -> None:
    """Test is_prod property."""
    config = Config(
        env=Environment.PROD,
        service=Service.ALPACA,
        base_url="https://api.alpaca.markets",
        alpaca_api_key="test",
        alpaca_secret_key="test",
        data_dir=None,  # type: ignore
        log_dir=None,  # type: ignore
        strategy_defaults=StrategyDefaults(),
    )
    assert config.is_paper is False
    assert config.is_prod is True


def test_load_config_defaults_to_paper() -> None:
    """Test load_config defaults to paper trading."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()

    assert config.env == Environment.PAPER
    assert config.service == Service.ALPACA
    assert "paper-api.alpaca.markets" in config.base_url


def test_load_config_prod_flag() -> None:
    """Test load_config with prod=True."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config(prod=True)

    assert config.env == Environment.PROD
    assert config.service == Service.ALPACA
    assert config.base_url == "https://api.alpaca.markets"


def test_load_config_service_alpaca() -> None:
    """Test load_config with explicit alpaca service."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config(service="alpaca")

    assert config.service == Service.ALPACA
