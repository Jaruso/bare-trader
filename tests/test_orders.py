"""Tests for basic order model and lifecycle."""

from decimal import Decimal
import pytest
from trader.models.order import Order, OrderSide, OrderType, OrderStatus


def test_order_creation():
    o = Order(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("10"), order_type=OrderType.MARKET)
    assert o.symbol == "AAPL"
    assert o.side == OrderSide.BUY
    assert o.qty == Decimal("10")
    assert o.order_type == OrderType.MARKET
    assert o.status == OrderStatus.NEW


def test_order_lifecycle():
    o = Order(symbol="AAPL", side=OrderSide.SELL, qty=Decimal("5"), order_type=OrderType.LIMIT, limit_price=Decimal("150"))
    assert o.status == OrderStatus.NEW
    o.mark_submitted("ext-123")
    assert o.status == OrderStatus.SUBMITTED
    assert o.external_id == "ext-123"
    o.mark_filled()
    assert o.status == OrderStatus.FILLED


def test_order_validation():
    o = Order(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("1"), order_type=OrderType.MARKET)
    o.validate()

    # invalid quantity
    with pytest.raises(ValueError):
        Order(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("0"), order_type=OrderType.MARKET).validate()

    # limit order requires limit_price
    with pytest.raises(ValueError):
        Order(symbol="AAPL", side=OrderSide.SELL, qty=Decimal("1"), order_type=OrderType.LIMIT).validate()


def test_order_persistence(tmp_path):
    from trader.oms.store import save_orders, load_orders

    o1 = Order(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("2"), order_type=OrderType.MARKET)
    o2 = Order(symbol="TSLA", side=OrderSide.SELL, qty=Decimal("3"), order_type=OrderType.LIMIT, limit_price=Decimal("400"))

    save_orders([o1, o2], tmp_path)
    loaded = load_orders(tmp_path)

    assert len(loaded) == 2
    assert loaded[0].symbol == "AAPL"
    assert loaded[1].symbol == "TSLA"
