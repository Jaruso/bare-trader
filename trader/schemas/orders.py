"""Order request and response schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from trader.api.broker import Order


class OrderRequest(BaseModel):
    """Input for placing an order."""

    symbol: str
    qty: int = Field(ge=1)
    price: Decimal = Field(gt=0)
    side: str  # "buy" or "sell"
    order_type: str = "limit"


class OrderResponse(BaseModel):
    """Order information."""

    id: str
    symbol: str
    side: str
    order_type: str
    qty: Decimal
    status: str
    filled_qty: Decimal = Decimal("0")
    filled_avg_price: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    trail_percent: Decimal | None = None
    created_at: str | None = None

    @classmethod
    def from_domain(cls, order: Order) -> OrderResponse:
        return cls(
            id=order.id,
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.order_type.value,
            qty=order.qty,
            status=order.status.value,
            filled_qty=order.filled_qty,
            filled_avg_price=order.filled_avg_price,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            trail_percent=order.trail_percent,
            created_at=order.created_at,
        )
