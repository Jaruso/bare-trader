"""Tests for notification formatters."""

from datetime import datetime

from trader.notifications.formatters import (
    TradeNotification,
    format_error_plain,
    format_trade_plain,
)


def test_format_trade_plain_opened() -> None:
    """Trade opened message includes symbol, side, qty, price, strategy."""
    trade = TradeNotification(
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=150.25,
        strategy_name="trailing-stop",
        timestamp=datetime(2024, 12, 1, 10, 30, 0),
        event="trade_opened",
    )
    msg = format_trade_plain(trade)
    assert "AAPL" in msg
    assert "Opened" in msg
    assert "BUY" in msg
    assert "10" in msg
    assert "150.25" in msg
    assert "trailing-stop" in msg
    assert "2024-12-01" in msg


def test_format_trade_plain_closed() -> None:
    """Trade closed uses Closed and sell side."""
    trade = TradeNotification(
        symbol="GOOGL",
        side="sell",
        quantity=5,
        price=142.50,
        strategy_name="bracket",
        event="trade_closed",
    )
    msg = format_trade_plain(trade)
    assert "Closed" in msg
    assert "GOOGL" in msg
    assert "SELL" in msg


def test_format_error_plain() -> None:
    """Error formatter includes exception type and message."""
    msg = format_error_plain(ValueError("invalid symbol"))
    assert "Error" in msg
    assert "ValueError" in msg
    assert "invalid symbol" in msg
