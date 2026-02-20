"""Data and safety service functions."""

from __future__ import annotations

from trader.app import get_broker
from trader.core.safety import SafetyCheck, SafetyLimits
from trader.data.ledger import TradeLedger
from trader.utils.config import Config


def get_safety_status(config: Config) -> dict[str, object]:
    """Get safety controls status.

    Args:
        config: Application configuration.

    Returns:
        Dict with safety status and limits.

    Raises:
        ConfigurationError: If API keys not configured.
    """
    broker = get_broker(config)
    ledger = TradeLedger()
    checker = SafetyCheck(broker, ledger)

    status = checker.get_status()
    limits = SafetyLimits()

    return {
        "status": status,
        "limits": {
            "max_position_size": limits.max_position_size,
            "max_position_value": str(limits.max_position_value),
            "max_order_value": str(limits.max_order_value),
            "max_daily_loss": str(limits.max_daily_loss),
            "max_daily_trades": limits.max_daily_trades,
        },
    }
