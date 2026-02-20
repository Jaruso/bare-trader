"""Optimization engine for strategy parameters."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

import pandas as pd

from trader.backtest import BacktestEngine, HistoricalBroker, load_data_for_backtest
from trader.optimization.objectives import score_result
from trader.optimization.results import OptimizationResult, new_result_id
from trader.optimization.search import generate_grid, generate_random
from trader.utils.logging import get_logger


class Optimizer:
    """Optimizes strategy parameters using backtesting."""

    def __init__(
        self,
        strategy_type: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        objective: str = "total_return_pct",
        data_source: str = "csv",
        data_dir: str | None = None,
        initial_capital: float = 100000.0,
        historical_data: dict[str, pd.DataFrame] | None = None,
    ) -> None:
        self.strategy_type = strategy_type
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.objective = objective
        self.data_source = data_source
        self.data_dir = data_dir
        self.initial_capital = Decimal(str(initial_capital))
        self.historical_data = historical_data
        self.logger = get_logger("trader.optimization")

    def optimize(
        self,
        param_grid: dict[str, list[Any]],
        method: str = "grid",
        num_samples: int | None = None,
    ) -> OptimizationResult:
        """Run parameter optimization."""
        if method == "grid":
            param_sets = generate_grid(param_grid)
        elif method == "random":
            if num_samples is None:
                raise ValueError("num_samples is required for random search")
            param_sets = generate_random(param_grid, num_samples)
        else:
            raise ValueError(f"Unknown optimization method: {method}")

        if not param_sets:
            raise ValueError("No parameter combinations to evaluate")

        start_time = perf_counter()
        best_score = None
        best_params = None
        best_backtest = None
        results_summary: list[dict[str, Any]] = []

        for params in param_sets:
            backtest_result = self._run_single_backtest(params)
            score = score_result(backtest_result, self.objective)
            results_summary.append(
                {
                    "params": params,
                    "score": score,
                    "backtest_id": backtest_result.id,
                }
            )

            if best_score is None or score > best_score:
                best_score = score
                best_params = params
                best_backtest = backtest_result

        if best_score is None or best_params is None or best_backtest is None:
            raise ValueError("Optimization failed to produce any results")

        runtime = perf_counter() - start_time

        return OptimizationResult(
            id=new_result_id(),
            strategy_type=self.strategy_type,
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            created_at=datetime.now(),
            objective=self.objective,
            method=method,
            best_params=best_params,
            best_score=best_score,
            best_backtest=best_backtest,
            all_results=results_summary,
            num_combinations=len(param_sets),
            runtime_seconds=runtime,
        )

    def _run_single_backtest(self, params: dict[str, Any]):
        strategy_config = _build_strategy_config(
            strategy_type=self.strategy_type,
            symbol=self.symbol,
            params=params,
        )

        historical_data = self.historical_data
        if historical_data is None:
            historical_data = load_data_for_backtest(
                symbols=[self.symbol],
                start_date=self.start_date,
                end_date=self.end_date,
                data_source=self.data_source,
                data_dir=self.data_dir,
            )

        broker = HistoricalBroker(
            historical_data=historical_data,
            initial_cash=self.initial_capital,
        )

        engine = BacktestEngine(
            broker=broker,
            strategy_config=strategy_config,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        return engine.run()


def _build_strategy_config(
    strategy_type: str, symbol: str, params: dict[str, Any]
) -> dict:
    config = {
        "symbol": symbol,
    }

    if strategy_type in ("trailing-stop", "trailing_stop"):
        config["strategy_type"] = "trailing_stop"
        config["quantity"] = int(params.get("quantity", 10))
        if "trailing_stop_pct" not in params:
            raise ValueError("trailing_stop_pct is required for trailing-stop optimization")
        config["trailing_stop_pct"] = str(params["trailing_stop_pct"])
        return config

    if strategy_type == "bracket":
        config["strategy_type"] = "bracket"
        config["quantity"] = int(params.get("quantity", 10))
        if "take_profit_pct" not in params or "stop_loss_pct" not in params:
            raise ValueError("take_profit_pct and stop_loss_pct are required for bracket")
        config["take_profit_pct"] = str(params["take_profit_pct"])
        config["stop_loss_pct"] = str(params["stop_loss_pct"])
        return config

    raise ValueError(f"Unsupported strategy type: {strategy_type}")
