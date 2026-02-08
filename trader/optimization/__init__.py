"""Optimization module for AutoTrader."""

from trader.optimization.objectives import OBJECTIVES, score_result
from trader.optimization.optimizer import Optimizer
from trader.optimization.results import OptimizationResult
from trader.optimization.store import (
    delete_optimization,
    get_optimizations_dir,
    list_optimizations,
    load_optimization,
    save_optimization,
)

__all__ = [
    "Optimizer",
    "OptimizationResult",
    "OBJECTIVES",
    "score_result",
    "save_optimization",
    "load_optimization",
    "list_optimizations",
    "delete_optimization",
    "get_optimizations_dir",
]
