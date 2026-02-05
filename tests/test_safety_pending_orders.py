"""Tests for safety checks that consider pending orders saved to orders.yaml."""
from decimal import Decimal
from pathlib import Path

from trader.core.safety import SafetyCheck, SafetyLimits
from trader.data.ledger import TradeLedger
from trader.oms.store import save_orders
from trader.models.order import Order as LocalOrder, OrderSide, OrderType, OrderStatus


class MockBroker:
    def __init__(self, position_qty=Decimal("0"), position_value=Decimal("0"), buying_power=Decimal("10000")):
        self._position_qty = position_qty
        self._position_value = position_value
        self._account = type("A", (), {"cash": Decimal("10000"), "buying_power": buying_power, "equity": Decimal("0"), "currency": "USD"})

    def get_position(self, symbol: str):
        if self._position_qty == 0:
            return None
        return type("P", (), {"qty": self._position_qty, "market_value": self._position_value})

    def get_account(self):
        return self._account

    def get_quote(self, symbol: str):
        return type("Q", (), {"bid": Decimal("99"), "ask": Decimal("101"), "last": Decimal("100"), "volume": 1000})


class DummyLedger(TradeLedger):
    def __init__(self):
        # do not call super
        pass

    def get_total_today_pnl(self):
        return Decimal("0")

    def get_trade_count_today(self):
        return 0


def test_pending_buys_reduce_buying_power(tmp_path: Path):
    # Create a pending buy order for 50 shares @ limit 100 (value 5000)
    o = LocalOrder(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("50"), order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    save_orders([o], tmp_path)

    broker = MockBroker(position_qty=Decimal("0"), position_value=Decimal("0"), buying_power=Decimal("6000"))
    ledger = DummyLedger()
    limits = SafetyLimits(max_position_value=Decimal("100000"))
    checker = SafetyCheck(broker, ledger, limits=limits, orders_dir=tmp_path)

    # Attempt to place a new buy for 20 shares @ 100 (value 2000). Available buying power = 6000 - 5000 = 1000 -> should be blocked
    allowed, reason = checker.check_order("AAPL", 20, Decimal("100"), is_buy=True)
    assert allowed is False
    assert "Insufficient buying power" in reason


def test_pending_buys_count_toward_position_size(tmp_path: Path):
    # Create a pending buy for 60 shares
    o = LocalOrder(symbol="AAPL", side=OrderSide.BUY, qty=Decimal("60"), order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    save_orders([o], tmp_path)

    broker = MockBroker(position_qty=Decimal("10"), position_value=Decimal("1000"), buying_power=Decimal("20000"))
    ledger = DummyLedger()
    limits = SafetyLimits(max_position_value=Decimal("100000"))
    checker = SafetyCheck(broker, ledger, limits=limits, orders_dir=tmp_path)

    # Max position size default is 100. Existing 10 + pending 60 + new 40 = 110 > 100 -> should be blocked
    allowed, reason = checker.check_order("AAPL", 40, Decimal("100"), is_buy=True)
    assert allowed is False
    assert "exceeds position size limit" in reason
