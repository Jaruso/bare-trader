"""Optimization orchestration service functions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from trader.errors import ValidationError
from trader.schemas.optimization import OptimizeRequest, OptimizeResponse
from trader.utils.config import Config

# Canonical parameter name aliases
_PARAM_ALIAS_MAP = {
    "trail_percent": "trailing_stop_pct",
    "trailing_pct": "trailing_stop_pct",
    "trailing_stop_pct": "trailing_stop_pct",
    "take_profit": "take_profit_pct",
    "take_profit_pct": "take_profit_pct",
    "stop_loss": "stop_loss_pct",
    "stop_loss_pct": "stop_loss_pct",
    "qty": "quantity",
    "quantity": "quantity",
}


def _normalize_param_keys(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize CLI/MCP-friendly param names to internal format.

    Converts short names like 'take_profit' and 'stop_loss' to their
    canonical '_pct' forms expected by validation and optimization.

    Args:
        params: Parameter dictionary with potentially aliased keys.

    Returns:
        Normalized parameter dictionary with canonical keys.
    """
    normalized = {}
    for key, value in params.items():
        canonical_key = _PARAM_ALIAS_MAP.get(key, key)
        # If both alias and canonical exist, prefer canonical
        if canonical_key not in normalized:
            normalized[canonical_key] = value
    return normalized


def run_optimization(config: Config, request: OptimizeRequest) -> OptimizeResponse:
    """Run strategy parameter optimization.

    Args:
        config: Application configuration.
        request: Optimization request schema.

    Returns:
        Optimization response schema.

    Raises:
        ValidationError: If parameters are invalid.
    """
    from trader.optimization import Optimizer, save_optimization

    # Parse dates
    try:
        start_date = datetime.strptime(request.start, "%Y-%m-%d")
        end_date = datetime.strptime(request.end, "%Y-%m-%d")
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid date format: {e}",
            code="INVALID_DATE_FORMAT",
            suggestion="Use YYYY-MM-DD format",
        )

    # Normalize param keys before validation (e.g. take_profit -> take_profit_pct)
    normalized_params = _normalize_param_keys(request.params)

    # Validate param grid
    _validate_optimization_params(request.strategy_type, normalized_params)

    # Create optimizer
    optimizer = Optimizer(
        strategy_type=request.strategy_type,
        symbol=request.symbol,
        start_date=start_date,
        end_date=end_date,
        objective=request.objective,
        data_source=request.data_source,
        data_dir=request.data_dir,
        initial_capital=request.initial_capital,
    )

    try:
        result = optimizer.optimize(
            param_grid=normalized_params,
            method=request.method,
            num_samples=request.num_samples,
        )
    except Exception as e:
        raise ValidationError(
            message=f"Optimization failed: {e}",
            code="OPTIMIZATION_FAILED",
        )

    # Save if requested
    if request.save:
        save_optimization(result)

    return OptimizeResponse.from_domain(result)


def _validate_optimization_params(strategy_type: str, param_grid: dict[str, Any]) -> None:
    """Validate optimization parameters for the given strategy type.

    Raises:
        ValidationError: If required parameters are missing.
    """
    if strategy_type == "trailing-stop":
        if "trailing_stop_pct" not in param_grid:
            raise ValidationError(
                message="trailing_stop_pct is required for trailing-stop optimization",
                code="MISSING_PARAM",
                details={"required": "trailing_stop_pct"},
            )
    elif strategy_type == "bracket":
        missing = []
        if "take_profit_pct" not in param_grid:
            missing.append("take_profit_pct")
        if "stop_loss_pct" not in param_grid:
            missing.append("stop_loss_pct")
        if missing:
            raise ValidationError(
                message=f"Missing required parameters: {', '.join(missing)}",
                code="MISSING_PARAM",
                details={"required": missing},
            )
