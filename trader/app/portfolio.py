"""Portfolio, account, positions, and quote service functions."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from trader.app import get_broker
from trader.errors import BrokerError
from trader.schemas.portfolio import (
    AccountInfo,
    BalanceResponse,
    PortfolioResponse,
    PositionInfo,
    QuoteResponse,
)
from trader.strategies.loader import load_strategies
from trader.utils.config import Config


def get_balance(config: Config) -> BalanceResponse:
    """Get account balance overview.

    Args:
        config: Application configuration.

    Returns:
        Balance response with account, positions, and market status.

    Raises:
        ConfigurationError: If API keys not configured.
        BrokerError: If broker call fails.
    """
    try:
        broker = get_broker(config)
        account = broker.get_account()
        positions_list = broker.get_positions()
        market_open = broker.is_market_open()
    except Exception as e:
        if "ConfigurationError" in type(e).__name__:
            raise
        raise BrokerError(
            message=f"Failed to fetch account data: {e}",
            code="BROKER_FETCH_FAILED",
        )

    total_value = sum((p.market_value for p in positions_list), Decimal("0"))
    total_pl = sum((p.unrealized_pl for p in positions_list), Decimal("0"))

    day_change = None
    day_change_pct = None
    if account.last_equity:
        day_change = account.equity - account.last_equity
        day_change_pct = (
            (day_change / account.last_equity) * 100 if account.last_equity else Decimal("0")
        )

    return BalanceResponse(
        account=AccountInfo.from_domain(account),
        positions=[PositionInfo.from_domain(p) for p in positions_list],
        market_open=market_open,
        total_positions_value=total_value,
        total_unrealized_pl=total_pl,
        day_change=day_change,
        day_change_pct=day_change_pct,
    )


def get_positions(config: Config) -> list[PositionInfo]:
    """Get open positions.

    Args:
        config: Application configuration.

    Returns:
        List of position info schemas.
    """
    broker = get_broker(config)
    positions_list = broker.get_positions()
    return [PositionInfo.from_domain(p) for p in positions_list]


def get_portfolio_summary(config: Config) -> PortfolioResponse:
    """Get portfolio summary with detailed position breakdown.

    Args:
        config: Application configuration.

    Returns:
        Portfolio response schema.
    """
    from trader.core.portfolio import Portfolio
    from trader.data.ledger import TradeLedger

    broker = get_broker(config)
    ledger = TradeLedger()
    pf = Portfolio(broker, ledger)

    summary = pf.get_summary()
    positions = pf.get_positions_detail()

    return PortfolioResponse.from_domain(summary, positions)


def get_quote(config: Config, symbol: str) -> QuoteResponse:
    """Get current market quote.

    Args:
        config: Application configuration.
        symbol: Stock symbol.

    Returns:
        Quote response schema.
    """
    broker = get_broker(config)
    q = broker.get_quote(symbol.upper())
    return QuoteResponse.from_domain(q)


def scan_symbols(
    config: Config,
    symbols: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan symbols for current prices and strategy info.

    Args:
        config: Application configuration.
        symbols: List of symbols to scan. If None, uses strategy symbols.

    Returns:
        List of dicts with symbol scan data.
    """
    broker = get_broker(config)
    strategies = load_strategies()

    if not symbols:
        symbols = list(set(s.symbol for s in strategies))

    if not symbols:
        return []

    results = []
    for symbol in symbols:
        symbol = symbol.upper()
        try:
            q = broker.get_quote(symbol)
            mid = (q.bid + q.ask) / 2
            spread = q.ask - q.bid
            spread_pct = (spread / mid * 100) if mid > 0 else Decimal("0")

            symbol_strategies = [s for s in strategies if s.symbol == symbol]
            strat_strs = [
                f"{s.strategy_type.value}: {s.phase.value}"
                for s in symbol_strategies
            ]

            results.append({
                "symbol": symbol,
                "bid": str(q.bid),
                "ask": str(q.ask),
                "spread": str(spread),
                "spread_pct": str(spread_pct),
                "strategies": strat_strs,
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e),
            })

    return results


def watch_strategies(config: Config) -> list[dict[str, Any]]:
    """Watch prices for symbols in configured strategies.

    Args:
        config: Application configuration.

    Returns:
        List of dicts with watch data per symbol.
    """
    broker = get_broker(config)
    strategies = load_strategies()

    if not strategies:
        return []

    symbols = list(set(s.symbol for s in strategies))
    results = []

    for symbol in symbols:
        try:
            q = broker.get_quote(symbol)
            symbol_strategies = [s for s in strategies if s.symbol == symbol]
            strat_strs = [
                f"{s.strategy_type.value}: {s.phase.value.replace('_', ' ')}"
                for s in symbol_strategies
            ]
            results.append({
                "symbol": symbol,
                "bid": str(q.bid),
                "ask": str(q.ask),
                "strategies": strat_strs,
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e),
            })

    return results
