"""Optimization module for BareTrader."""

from baretrader.optimization.objectives import OBJECTIVES, score_result
from baretrader.optimization.optimizer import Optimizer
from baretrader.optimization.results import OptimizationResult
from baretrader.optimization.store import (
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
