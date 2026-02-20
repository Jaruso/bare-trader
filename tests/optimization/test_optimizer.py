"""Tests for optimization framework."""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from trader.backtest.results import BacktestResult
from trader.optimization.objectives import score_result
from trader.optimization.optimizer import Optimizer
from trader.optimization.search import generate_grid, generate_random


def _sample_data() -> dict[str, pd.DataFrame]:
    index = pd.date_range("2024-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "open": [100 + i for i in range(10)],
            "high": [101 + i for i in range(10)],
            "low": [99 + i for i in range(10)],
            "close": [100.5 + i for i in range(10)],
            "volume": [1000000 for _ in range(10)],
        },
        index=index,
    )
    return {"AAPL": df}


def test_generate_grid() -> None:
    grid = generate_grid({"a": [1, 2], "b": ["x", "y"]})
    assert len(grid) == 4
    assert {"a": 1, "b": "x"} in grid


def test_generate_random() -> None:
    samples = generate_random({"a": [1, 2, 3]}, num_samples=2, seed=42)
    assert len(samples) == 2
    assert all("a" in sample for sample in samples)


def test_score_result_total_return_pct() -> None:
    result = BacktestResult(
        id="t1",
        strategy_type="trailing_stop",
        symbol="AAPL",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        created_at=datetime(2024, 1, 11),
        strategy_config={},
        initial_capital=Decimal("100000"),
        total_return=Decimal("5000"),
        total_return_pct=Decimal("5"),
        win_rate=Decimal("50"),
        profit_factor=Decimal("1.2"),
        max_drawdown=Decimal("1000"),
        max_drawdown_pct=Decimal("2"),
        sharpe_ratio=None,
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        avg_win=Decimal("5000"),
        avg_loss=Decimal("0"),
        largest_win=Decimal("5000"),
        largest_loss=Decimal("0"),
        equity_curve=[],
        trades=[],
    )
    assert score_result(result, "total_return_pct") == Decimal("5")


def test_optimizer_grid_search() -> None:
    optimizer = Optimizer(
        strategy_type="trailing-stop",
        symbol="AAPL",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        objective="total_return_pct",
        historical_data=_sample_data(),
    )

    result = optimizer.optimize(
        param_grid={"trailing_stop_pct": [Decimal("2"), Decimal("3")]},
        method="grid",
    )

    assert result.num_combinations == 2
    assert result.best_params["trailing_stop_pct"] in (
        Decimal("2"),
        Decimal("3"),
    )
