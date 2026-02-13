"""Indicator service functions."""

from __future__ import annotations

from trader.errors import NotFoundError
from trader.schemas.indicators import IndicatorInfo


def list_all_indicators() -> list[IndicatorInfo]:
    """List all available technical indicators.

    Returns:
        List of indicator info schemas.
    """
    from trader.indicators import list_indicators

    return [IndicatorInfo.from_domain(spec) for spec in list_indicators()]


def describe_indicator(name: str) -> IndicatorInfo:
    """Get detailed info for a specific indicator.

    Args:
        name: Indicator name (e.g. "sma", "rsi").

    Returns:
        Indicator info schema.

    Raises:
        NotFoundError: If indicator name is unknown.
    """
    from trader.indicators import get_indicator

    try:
        indicator_obj = get_indicator(name)
    except ValueError:
        raise NotFoundError(
            message=f"Unknown indicator: {name}",
            code="INDICATOR_NOT_FOUND",
            suggestion="Use list_indicators (MCP) or 'trader indicator list' (CLI) to see available indicators",
        )

    return IndicatorInfo.from_domain(indicator_obj.spec)
