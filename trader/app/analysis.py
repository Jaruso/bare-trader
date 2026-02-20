"""Trade analysis service functions."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from baretrader.data.ledger import TradeLedger
from baretrader.schemas.analysis import AnalysisResponse


def analyze_trade_performance(
    symbol: str | None = None,
    days: int = 30,
    limit: int = 1000,
) -> AnalysisResponse | None:
    """Analyze trade performance.

    Args:
        symbol: Filter by symbol (or None for all).
        days: Analyze trades from last N days.
        limit: Max trades to analyze.

    Returns:
        Analysis response schema, or None if no trades found.
    """
    from baretrader.analysis.trades import analyze_trades

    ledger = TradeLedger()
    since = datetime.now() - timedelta(days=days)
    trades = ledger.get_trades(symbol=symbol, since=since, limit=limit)

    if not trades:
        return None

    report = analyze_trades(trades)
    return AnalysisResponse.from_domain(report)


def get_trade_history(
    symbol: str | None = None,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Get trade history records.

    Args:
        symbol: Filter by symbol (or None for all).
        limit: Max number of trades.

    Returns:
        List of trade record dicts.
    """
    ledger = TradeLedger()
    trades = ledger.get_trades(symbol=symbol, limit=limit)

    return [
        {
            "id": trade.id,
            "order_id": trade.order_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": str(trade.quantity),
            "price": str(trade.price),
            "total": str(trade.total),
            "status": trade.status,
            "rule_id": trade.rule_id,
            "timestamp": trade.timestamp.isoformat(),
        }
        for trade in trades
    ]


def get_today_pnl() -> Decimal:
    """Get today's realized P/L.

    Returns:
        Decimal P/L value.
    """
    ledger = TradeLedger()
    return ledger.get_total_today_pnl()
