"""Optimization request and response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from trader.optimization.results import OptimizationResult

from trader.schemas.backtests import BacktestResponse


class OptimizeRequest(BaseModel):
    """Input for running parameter optimization."""

    strategy_type: str
    symbol: str
    start: str  # YYYY-MM-DD
    end: str  # YYYY-MM-DD
    params: dict[str, list[Any]]
    objective: str = "total_return_pct"
    method: str = "grid"
    num_samples: int | None = None
    data_source: str = "csv"
    data_dir: str | None = None
    initial_capital: float = Field(default=100000.0, gt=0)
    save: bool = True


class OptimizeResponse(BaseModel):
    """Optimization result."""

    id: str
    strategy_type: str
    symbol: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    objective: str
    method: str
    best_params: dict[str, Any]
    best_score: Decimal
    best_backtest: BacktestResponse
    all_results: list[dict[str, Any]] = []
    num_combinations: int = 0
    runtime_seconds: float = 0.0

    @classmethod
    def from_domain(cls, r: OptimizationResult) -> OptimizeResponse:
        return cls(
            id=r.id,
            strategy_type=r.strategy_type,
            symbol=r.symbol,
            start_date=r.start_date,
            end_date=r.end_date,
            created_at=r.created_at,
            objective=r.objective,
            method=r.method,
            best_params=r.best_params,
            best_score=r.best_score,
            best_backtest=BacktestResponse.from_domain(r.best_backtest),
            all_results=[
                {
                    "params": entry["params"],
                    "score": str(entry["score"]),
                    "backtest_id": entry["backtest_id"],
                }
                for entry in r.all_results
            ],
            num_combinations=r.num_combinations,
            runtime_seconds=r.runtime_seconds,
        )
