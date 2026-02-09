"""Trade analysis schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from trader.analysis.trades import OpenPosition, TradeAnalysisReport, TradeStats


class TradeStatsSchema(BaseModel):
    """Trade performance statistics."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    avg_hold_minutes: Decimal

    @classmethod
    def from_domain(cls, stats: TradeStats) -> TradeStatsSchema:
        return cls(
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            losing_trades=stats.losing_trades,
            win_rate=stats.win_rate,
            gross_profit=stats.gross_profit,
            gross_loss=stats.gross_loss,
            net_profit=stats.net_profit,
            profit_factor=stats.profit_factor,
            avg_win=stats.avg_win,
            avg_loss=stats.avg_loss,
            largest_win=stats.largest_win,
            largest_loss=stats.largest_loss,
            avg_hold_minutes=stats.avg_hold_minutes,
        )


class OpenPositionSchema(BaseModel):
    """An unmatched open position."""

    symbol: str
    lots: int
    quantity: Decimal
    avg_cost: Decimal

    @classmethod
    def from_domain(cls, pos: OpenPosition) -> OpenPositionSchema:
        return cls(
            symbol=pos.symbol,
            lots=pos.lots,
            quantity=pos.quantity,
            avg_cost=pos.avg_cost,
        )


class AnalysisResponse(BaseModel):
    """Full trade analysis report."""

    summary: TradeStatsSchema
    per_symbol: dict[str, TradeStatsSchema]
    open_positions: list[OpenPositionSchema]
    unmatched_sell_qty: dict[str, Decimal]

    @classmethod
    def from_domain(cls, report: TradeAnalysisReport) -> AnalysisResponse:
        return cls(
            summary=TradeStatsSchema.from_domain(report.summary),
            per_symbol={
                sym: TradeStatsSchema.from_domain(stats)
                for sym, stats in report.per_symbol.items()
            },
            open_positions=[
                OpenPositionSchema.from_domain(pos)
                for pos in report.open_positions
            ],
            unmatched_sell_qty=report.unmatched_sell_qty,
        )
