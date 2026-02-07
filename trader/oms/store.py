"""Simple order persistence (YAML) for the OMS scaffold."""
from pathlib import Path
from typing import Optional
import yaml

from trader.models.order import Order


def get_orders_file(config_dir: Optional[Path] = None) -> Path:
    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "orders.yaml"


def save_orders(orders: list[Order], config_dir: Optional[Path] = None) -> None:
    path = get_orders_file(config_dir)
    data = {"orders": [o.to_dict() for o in orders]}
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_orders(config_dir: Optional[Path] = None) -> list[Order]:
    path = get_orders_file(config_dir)
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    items = data.get("orders", [])
    return [Order.from_dict(i) for i in items]


def _to_local_order(order_obj: object) -> Order:
    """Convert a broker.Order-like object or local Order dict to local `Order` model."""
    # Import local enums
    from trader.models.order import Order as LocalOrder, OrderSide as LocalSide, OrderType as LocalType, OrderStatus as LocalStatus

    # Extract fields with fallbacks
    oid = getattr(order_obj, "id", getattr(order_obj, "order_id", ""))
    symbol = getattr(order_obj, "symbol")
    qty = getattr(order_obj, "qty")
    # Side may be enum or string
    side_raw = getattr(order_obj, "side")
    try:
        side = LocalSide(side_raw.value) if hasattr(side_raw, "value") else LocalSide(side_raw)
    except Exception:
        side = LocalSide.BUY

    ot_raw = getattr(order_obj, "order_type", getattr(order_obj, "orderType", None))
    try:
        order_type = LocalType(ot_raw.value) if hasattr(ot_raw, "value") else LocalType(ot_raw)
    except Exception:
        order_type = LocalType.MARKET

    limit_price = getattr(order_obj, "limit_price", None)
    external_id = getattr(order_obj, "external_id", None)

    status_raw = getattr(order_obj, "status", None)
    try:
        status = LocalStatus(status_raw.value) if hasattr(status_raw, "value") else LocalStatus(status_raw)
    except Exception:
        status = LocalStatus.NEW

    return LocalOrder(
        id=oid or "",
        symbol=symbol,
        side=side,
        qty=qty,
        order_type=order_type,
        limit_price=limit_price,
        external_id=external_id,
        status=status,
    )


def save_order(order_obj: object, config_dir: Optional[Path] = None) -> None:
    """Save or update a single order to the orders file.

    Accepts either a local `Order` instance or a broker-like Order object.
    """
    orders = load_orders(config_dir)

    local = order_obj if isinstance(order_obj, Order) else _to_local_order(order_obj)

    # Replace existing by id if found
    replaced = False
    for i, o in enumerate(orders):
        # Replace when IDs match, or when external IDs match (broker vs local mapping)
        if (
            (o.id and local.id and o.id == local.id)
            or (o.external_id and local.external_id and o.external_id == local.external_id)
            or (o.external_id and local.id and o.external_id == local.id)
            or (o.id and local.external_id and o.id == local.external_id)
        ):
            orders[i] = local
            replaced = True
            break

    if not replaced:
        orders.append(local)

    save_orders(orders, config_dir)
