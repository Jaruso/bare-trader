"""Tests for TradingEngine order reconciliation with broker."""
from decimal import Decimal
from pathlib import Path

from trader.api.broker import Order as BrokerOrder
from trader.api.broker import OrderSide, OrderType
from trader.api.broker import OrderStatus as BrokerOrderStatus
from trader.models.order import Order as LocalOrder
from trader.oms.store import load_orders, save_orders


class MockBroker:
    def __init__(self, orders_map=None):
        # orders_map: id -> BrokerOrder
        self.orders_map = orders_map or {}

    def is_market_open(self):
        return True

    def get_order(self, order_id: str):
        return self.orders_map.get(order_id)


def test_reconcile_updates_persisted_order(tmp_path: Path):
    # Create a persisted local order with id 'o1' status NEW and external id 'ext-1'
    local = LocalOrder(id="o1", symbol="AAPL", side=OrderSide.BUY, qty=Decimal("1"), order_type=OrderType.MARKET, external_id="ext-1")
    # Save using store
    save_orders([local], tmp_path)

    # Broker reports external order as filled
    broker_order = BrokerOrder(
        id="ext-1",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        qty=Decimal("1"),
        status=BrokerOrderStatus.FILLED,
    )

    mock = MockBroker(orders_map={"o1": broker_order, "ext-1": broker_order})

    # Create engine configured to use tmp_path for orders
    from trader.core.engine import TradingEngine as EngineClass
    engine = EngineClass(mock, orders_dir=tmp_path)

    # Reconcile using tmp_path as config dir by setting engine attribute orders_dir via monkeypatching load_orders
    # We'll temporarily monkeypatch trader.oms.store.load_orders and save_order to use tmp_path
    # direct import path
    import trader.oms.store as store

    # Backup
    orig_load = store.load_orders
    orig_save = store.save_order

    try:
        import importlib
        engmod = importlib.import_module("trader.core.engine")
        # Monkeypatch engine module's load/save to point to tmp_path
        engmod.load_orders = lambda config_dir=None: load_orders(tmp_path)
        engmod.save_order = lambda order_obj, config_dir=None: orig_save(order_obj, tmp_path)

        engine._reconcile_orders()

        updated = load_orders(tmp_path)
        assert updated, "No orders persisted after reconcile"
        # Since broker reported FILLED, the persisted order status should be FILLED
        assert updated[0].status.value == BrokerOrderStatus.FILLED.value

    finally:
        store.load_orders = orig_load
        store.save_order = orig_save
