"""Application service layer for BareTrader.

This module provides the shared business logic used by both CLI and MCP
interfaces. Each submodule exposes functions that:
1. Accept validated input (Pydantic schemas or primitives)
2. Coordinate existing domain modules (broker, strategies, backtest, etc.)
3. Return Pydantic response schemas
4. Raise typed errors from baretrader.errors on failure
"""

from __future__ import annotations

from baretrader.api.alpaca import AlpacaBroker
from baretrader.api.broker import Broker
from baretrader.errors import ConfigurationError
from baretrader.utils.config import Config


def get_broker(config: Config) -> Broker:
    """Create a broker instance from config.

    Args:
        config: Application configuration.

    Returns:
        Configured broker instance.

    Raises:
        ConfigurationError: If API keys are not configured.
    """
    if not config.alpaca_api_key:
        env_var = "ALPACA_PROD_API_KEY" if config.is_prod else "ALPACA_API_KEY"
        raise ConfigurationError(
            message=f"{env_var} not configured",
            code="API_KEY_MISSING",
            suggestion=f"Set {env_var} and the corresponding secret key in .env",
        )
    return AlpacaBroker(
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.is_paper,
    )
