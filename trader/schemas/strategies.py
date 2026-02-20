"""Strategy CRUD schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from trader.strategies.models import Strategy


class StrategyCreate(BaseModel):
    """Input for creating a strategy."""

    strategy_type: str  # trailing-stop, bracket, scale-out, grid, pullback-trailing
    symbol: str
    qty: int = Field(ge=1, default=1)
    trailing_pct: float | None = None
    pullback_pct: float | None = None  # for pullback-trailing: buy when price drops this % from high
    take_profit: float | None = None
    stop_loss: float | None = None
    entry_price: float | None = None  # limit entry
    levels: int | None = None  # grid levels


class StrategyResponse(BaseModel):
    """Full strategy information."""

    id: str
    symbol: str
    strategy_type: str
    phase: str
    quantity: int
    enabled: bool
    # Entry config
    entry_type: str
    entry_price: Decimal | None = None
    entry_condition: str | None = None
    # Exit config
    trailing_stop_pct: Decimal | None = None
    pullback_pct: Decimal | None = None
    pullback_reference_price: Decimal | None = None
    take_profit_pct: Decimal | None = None
    stop_loss_pct: Decimal | None = None
    scale_targets: list[dict[str, Any]] | None = None
    grid_config: dict[str, Any] | None = None
    # State tracking
    entry_order_id: str | None = None
    entry_fill_price: Decimal | None = None
    high_watermark: Decimal | None = None
    exit_order_ids: list[str] = []
    scale_state: list[dict[str, Any]] | None = None
    grid_state: list[dict[str, Any]] | None = None
    # Scheduling
    schedule_at: datetime | None = None
    schedule_enabled: bool = False
    # Metadata
    created_at: datetime
    updated_at: datetime
    notes: str | None = None

    @classmethod
    def from_domain(cls, s: Strategy) -> StrategyResponse:
        return cls(
            id=s.id,
            symbol=s.symbol,
            strategy_type=s.strategy_type.value,
            phase=s.phase.value,
            quantity=s.quantity,
            enabled=s.enabled,
            entry_type=s.entry_type.value,
            entry_price=s.entry_price,
            entry_condition=s.entry_condition,
            trailing_stop_pct=s.trailing_stop_pct,
            pullback_pct=s.pullback_pct,
            pullback_reference_price=s.pullback_reference_price,
            take_profit_pct=s.take_profit_pct,
            stop_loss_pct=s.stop_loss_pct,
            scale_targets=s.scale_targets,
            grid_config=s.grid_config,
            entry_order_id=s.entry_order_id,
            entry_fill_price=s.entry_fill_price,
            high_watermark=s.high_watermark,
            exit_order_ids=s.exit_order_ids,
            scale_state=s.scale_state,
            grid_state=s.grid_state,
            schedule_at=s.schedule_at,
            schedule_enabled=s.schedule_enabled,
            created_at=s.created_at,
            updated_at=s.updated_at,
            notes=s.notes,
        )


class StrategyListResponse(BaseModel):
    """List of strategies."""

    strategies: list[StrategyResponse]
    count: int
