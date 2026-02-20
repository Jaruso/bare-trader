"""Portfolio, account, position, and quote schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from baretrader.api.broker import Account, Position, Quote
    from baretrader.core.portfolio import PortfolioSummary, PositionDetail


class AccountInfo(BaseModel):
    """Account information."""

    cash: Decimal
    buying_power: Decimal
    equity: Decimal
    portfolio_value: Decimal
    currency: str = "USD"
    daytrade_count: int = 0
    day_trading_buying_power: Decimal | None = None
    last_equity: Decimal | None = None
    status: str = "ACTIVE"
    pattern_day_trader: bool = False

    @classmethod
    def from_domain(cls, account: Account) -> AccountInfo:
        return cls(
            cash=account.cash,
            buying_power=account.buying_power,
            equity=account.equity,
            portfolio_value=account.portfolio_value,
            currency=account.currency,
            daytrade_count=account.daytrade_count,
            day_trading_buying_power=account.day_trading_buying_power,
            last_equity=account.last_equity,
            status=account.status,
            pattern_day_trader=account.pattern_day_trader,
        )


class PositionInfo(BaseModel):
    """Open position information."""

    symbol: str
    qty: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    unrealized_pl_pct: Decimal

    @classmethod
    def from_domain(cls, pos: Position) -> PositionInfo:
        return cls(
            symbol=pos.symbol,
            qty=pos.qty,
            avg_entry_price=pos.avg_entry_price,
            current_price=pos.current_price,
            market_value=pos.market_value,
            unrealized_pl=pos.unrealized_pl,
            unrealized_pl_pct=pos.unrealized_pl_pct,
        )


class PositionDetailInfo(BaseModel):
    """Detailed position with weight and cost basis."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    weight_pct: Decimal

    @classmethod
    def from_domain(cls, detail: PositionDetail) -> PositionDetailInfo:
        return cls(
            symbol=detail.symbol,
            quantity=detail.quantity,
            avg_cost=detail.avg_cost,
            current_price=detail.current_price,
            market_value=detail.market_value,
            cost_basis=detail.cost_basis,
            unrealized_pnl=detail.unrealized_pnl,
            unrealized_pnl_pct=detail.unrealized_pnl_pct,
            weight_pct=detail.weight_pct,
        )


class PortfolioResponse(BaseModel):
    """Full portfolio summary."""

    total_equity: Decimal
    cash: Decimal
    positions_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    realized_pnl_today: Decimal
    total_pnl_today: Decimal
    position_count: int
    positions: list[PositionDetailInfo] = []

    @classmethod
    def from_domain(
        cls,
        summary: PortfolioSummary,
        positions: list[PositionDetail] | None = None,
    ) -> PortfolioResponse:

        pos_list = [PositionDetailInfo.from_domain(p) for p in (positions or [])]
        return cls(
            total_equity=summary.total_equity,
            cash=summary.cash,
            positions_value=summary.positions_value,
            unrealized_pnl=summary.unrealized_pnl,
            unrealized_pnl_pct=summary.unrealized_pnl_pct,
            realized_pnl_today=summary.realized_pnl_today,
            total_pnl_today=summary.total_pnl_today,
            position_count=summary.position_count,
            positions=pos_list,
        )


class QuoteResponse(BaseModel):
    """Market quote."""

    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    spread: Decimal

    @classmethod
    def from_domain(cls, quote: Quote) -> QuoteResponse:
        return cls(
            symbol=quote.symbol,
            bid=quote.bid,
            ask=quote.ask,
            last=quote.last,
            volume=quote.volume,
            spread=quote.ask - quote.bid,
        )


class BalanceResponse(BaseModel):
    """Balance overview (account + positions + market status)."""

    account: AccountInfo
    positions: list[PositionInfo]
    market_open: bool
    total_positions_value: Decimal
    total_unrealized_pl: Decimal
    day_change: Decimal | None = None
    day_change_pct: Decimal | None = None
