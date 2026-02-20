"""Tests for trade analysis module."""

from datetime import datetime, timedelta
from decimal import Decimal

from trader.analysis.trades import analyze_trades
from trader.data.ledger import TradeRecord


def _trade(
    *,
    trade_id: int,
    order_id: str,
    symbol: str,
    side: str,
    qty: str,
    price: str,
    ts: datetime,
) -> TradeRecord:
    return TradeRecord(
        id=trade_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
        quantity=Decimal(qty),
        price=Decimal(price),
        total=Decimal(qty) * Decimal(price),
        status="filled",
        rule_id=None,
        timestamp=ts,
    )


def test_analyze_trades_profit_and_open_lots() -> None:
    start = datetime(2025, 1, 1, 9, 30)
    trades = [
        _trade(
            trade_id=1,
            order_id="o1",
            symbol="AAPL",
            side="buy",
            qty="10",
            price="100",
            ts=start,
        ),
        _trade(
            trade_id=2,
            order_id="o2",
            symbol="AAPL",
            side="buy",
            qty="5",
            price="110",
            ts=start + timedelta(minutes=10),
        ),
        _trade(
            trade_id=3,
            order_id="o3",
            symbol="AAPL",
            side="sell",
            qty="12",
            price="120",
            ts=start + timedelta(minutes=40),
        ),
    ]

    report = analyze_trades(trades)

    assert report.summary.total_trades == 2
    assert report.summary.gross_profit == Decimal("220")
    assert report.summary.net_profit == Decimal("220")

    assert len(report.open_positions) == 1
    open_pos = report.open_positions[0]
    assert open_pos.symbol == "AAPL"
    assert open_pos.quantity == Decimal("3")
    assert open_pos.avg_cost == Decimal("110")


def test_analyze_trades_loss_stats() -> None:
    start = datetime(2025, 1, 2, 9, 30)
    trades = [
        _trade(
            trade_id=1,
            order_id="o1",
            symbol="TSLA",
            side="buy",
            qty="10",
            price="100",
            ts=start,
        ),
        _trade(
            trade_id=2,
            order_id="o2",
            symbol="TSLA",
            side="sell",
            qty="10",
            price="90",
            ts=start + timedelta(minutes=30),
        ),
    ]

    report = analyze_trades(trades)

    assert report.summary.total_trades == 1
    assert report.summary.winning_trades == 0
    assert report.summary.losing_trades == 1
    assert report.summary.gross_loss == Decimal("100")
    assert report.summary.net_profit == Decimal("-100")


def test_analyze_trades_per_symbol_stats() -> None:
    start = datetime(2025, 1, 3, 9, 30)
    trades = [
        _trade(
            trade_id=1,
            order_id="o1",
            symbol="AAPL",
            side="buy",
            qty="5",
            price="100",
            ts=start,
        ),
        _trade(
            trade_id=2,
            order_id="o2",
            symbol="AAPL",
            side="sell",
            qty="5",
            price="110",
            ts=start + timedelta(minutes=20),
        ),
        _trade(
            trade_id=3,
            order_id="o3",
            symbol="MSFT",
            side="buy",
            qty="2",
            price="200",
            ts=start,
        ),
        _trade(
            trade_id=4,
            order_id="o4",
            symbol="MSFT",
            side="sell",
            qty="2",
            price="190",
            ts=start + timedelta(minutes=15),
        ),
    ]

    report = analyze_trades(trades)

    assert report.per_symbol["AAPL"].net_profit == Decimal("50")
    assert report.per_symbol["MSFT"].net_profit == Decimal("-20")
