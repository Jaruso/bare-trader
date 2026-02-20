"""Backtest request and response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from trader.backtest.results import BacktestResult


class BacktestRequest(BaseModel):
    """Input for running a backtest."""

    strategy_type: str  # trailing-stop, bracket
    symbol: str
    start: str  # YYYY-MM-DD
    end: str  # YYYY-MM-DD
    qty: int = Field(ge=1, default=10)
    trailing_pct: float | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    data_source: str = "csv"
    data_dir: str | None = None
    initial_capital: float = Field(default=100000.0, gt=0)
    save: bool = True


class BacktestSummary(BaseModel):
    """Metadata-level view for listing backtests."""

    id: str
    strategy_type: str
    symbol: str
    start_date: str
    end_date: str
    total_return_pct: Decimal
    win_rate: Decimal
    total_trades: int
    max_drawdown_pct: Decimal
    created_at: str

    @classmethod
    def from_index_entry(cls, entry: dict[str, Any]) -> BacktestSummary:
        """Create from a backtest index entry dict."""
        return cls(
            id=entry["id"],
            strategy_type=entry["strategy_type"],
            symbol=entry["symbol"],
            start_date=entry["start_date"],
            end_date=entry["end_date"],
            total_return_pct=Decimal(entry["total_return_pct"]),
            win_rate=Decimal(entry["win_rate"]),
            total_trades=entry["total_trades"],
            max_drawdown_pct=Decimal(entry["max_drawdown_pct"]),
            created_at=entry["created_at"],
        )


class BacktestResponse(BaseModel):
    """Full backtest result."""

    id: str
    strategy_type: str
    symbol: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    strategy_config: dict[str, Any]
    initial_capital: Decimal
    # Performance metrics
    total_return: Decimal
    total_return_pct: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    sharpe_ratio: Decimal | None = None
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")
    # Time series
    equity_curve: list[tuple[str, str]] = []
    trades: list[dict[str, Any]] = []

    @classmethod
    def from_domain(cls, r: BacktestResult) -> BacktestResponse:
        return cls(
            id=r.id,
            strategy_type=r.strategy_type,
            symbol=r.symbol,
            start_date=r.start_date,
            end_date=r.end_date,
            created_at=r.created_at,
            strategy_config=r.strategy_config,
            initial_capital=r.initial_capital,
            total_return=r.total_return,
            total_return_pct=r.total_return_pct,
            win_rate=r.win_rate,
            profit_factor=r.profit_factor,
            max_drawdown=r.max_drawdown,
            max_drawdown_pct=r.max_drawdown_pct,
            sharpe_ratio=r.sharpe_ratio,
            total_trades=r.total_trades,
            winning_trades=r.winning_trades,
            losing_trades=r.losing_trades,
            avg_win=r.avg_win,
            avg_loss=r.avg_loss,
            largest_win=r.largest_win,
            largest_loss=r.largest_loss,
            equity_curve=[
                (ts.isoformat(), str(equity)) for ts, equity in r.equity_curve
            ],
            trades=r.trades,
        )
