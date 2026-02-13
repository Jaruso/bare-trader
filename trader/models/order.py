"""Order model for OMS scaffold."""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    NEW = "new"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELED = "canceled"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    qty: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    id: str = field(default_factory=lambda: "")
    external_id: str | None = None
    status: OrderStatus = OrderStatus.NEW

    def validate(self) -> None:
        """Validate order fields.

        Raises:
            ValueError: if validation fails.
        """
        if self.qty <= 0:
            raise ValueError("Quantity must be positive")

        if self.order_type == OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("Limit orders require a limit_price")
            if self.limit_price <= 0:
                raise ValueError("Limit price must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "qty": str(self.qty),
            "order_type": self.order_type.value,
            "limit_price": str(self.limit_price) if self.limit_price is not None else None,
            "external_id": self.external_id,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Order":
        lp = None
        if data.get("limit_price") is not None:
            lp = Decimal(str(data["limit_price"]))

        return cls(
            id=data.get("id", ""),
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            qty=Decimal(str(data["qty"])),
            order_type=OrderType(data["order_type"]),
            limit_price=lp,
            external_id=data.get("external_id"),
            status=OrderStatus(data.get("status", OrderStatus.NEW.value)),
        )

    def mark_submitted(self, external_id: str) -> None:
        self.external_id = external_id
        self.status = OrderStatus.SUBMITTED

    def mark_filled(self) -> None:
        self.status = OrderStatus.FILLED

    def mark_canceled(self) -> None:
        self.status = OrderStatus.CANCELED
