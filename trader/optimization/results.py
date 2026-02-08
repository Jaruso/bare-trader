"""Optimization results and serialization."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from trader.backtest.results import BacktestResult


@dataclass
class OptimizationResult:
    """Results from parameter optimization."""

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
    best_backtest: BacktestResult
    all_results: list[dict[str, Any]] = field(default_factory=list)
    num_combinations: int = 0
    runtime_seconds: float = 0.0

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to a DataFrame."""
        rows = []
        for entry in self.all_results:
            row = {"score": entry["score"], "backtest_id": entry["backtest_id"]}
            row.update(entry["params"])
            rows.append(row)
        return pd.DataFrame(rows)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "id": self.id,
            "strategy_type": self.strategy_type,
            "symbol": self.symbol,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "objective": self.objective,
            "method": self.method,
            "best_params": self.best_params,
            "best_score": str(self.best_score),
            "best_backtest": self.best_backtest.to_dict(),
            "all_results": [
                {
                    "params": entry["params"],
                    "score": str(entry["score"]),
                    "backtest_id": entry["backtest_id"],
                }
                for entry in self.all_results
            ],
            "num_combinations": self.num_combinations,
            "runtime_seconds": self.runtime_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OptimizationResult":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            strategy_type=data["strategy_type"],
            symbol=data["symbol"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            objective=data["objective"],
            method=data["method"],
            best_params=data["best_params"],
            best_score=Decimal(data["best_score"]),
            best_backtest=BacktestResult.from_dict(data["best_backtest"]),
            all_results=[
                {
                    "params": entry["params"],
                    "score": Decimal(entry["score"]),
                    "backtest_id": entry["backtest_id"],
                }
                for entry in data.get("all_results", [])
            ],
            num_combinations=data.get("num_combinations", 0),
            runtime_seconds=data.get("runtime_seconds", 0.0),
        )


def new_result_id() -> str:
    return str(uuid.uuid4())[:8]
