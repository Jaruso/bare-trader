"""Objective functions for optimization runs."""

from decimal import Decimal

from trader.backtest.results import BacktestResult


def score_result(result: BacktestResult, objective: str) -> Decimal:
    """Score a backtest result based on the requested objective."""
    if objective == "total_return":
        return result.total_return
    if objective == "total_return_pct":
        return result.total_return_pct
    if objective == "win_rate":
        return result.win_rate
    if objective == "profit_factor":
        return result.profit_factor
    if objective == "max_drawdown_pct":
        return Decimal("0") - result.max_drawdown_pct

    raise ValueError(f"Unknown objective: {objective}")


OBJECTIVES = {
    "total_return": "Maximize total return ($)",
    "total_return_pct": "Maximize total return (%)",
    "win_rate": "Maximize win rate (%)",
    "profit_factor": "Maximize profit factor",
    "max_drawdown_pct": "Minimize max drawdown (%)",
}
