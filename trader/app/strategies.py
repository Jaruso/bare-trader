"""Strategy CRUD service functions."""

from __future__ import annotations

from decimal import Decimal

from trader.audit import log_action as audit_log
from trader.errors import NotFoundError, ValidationError
from trader.schemas.strategies import (
    StrategyCreate,
    StrategyListResponse,
    StrategyResponse,
)
from trader.strategies.loader import (
    delete_strategy as _delete_strategy,
)
from trader.strategies.loader import (
    enable_strategy as _enable_strategy,
)
from trader.strategies.loader import (
    get_strategy as _get_strategy,
)
from trader.strategies.loader import (
    load_strategies,
)
from trader.strategies.loader import (
    save_strategy as _save_strategy,
)
from trader.strategies.models import (
    EntryType,
    Strategy,
    StrategyPhase,
    StrategyType,
)
from trader.utils.config import Config

def _to_pct(value: Decimal) -> Decimal:
    """Normalize a percentage value.

    Accepts both decimal form (0.05) and percentage form (5.0).
    Values less than 1 are treated as decimal and converted to percentage.
    """
    if value < 1:
        return value * Decimal("100")
    return value


# Map from CLI-style names to StrategyType enums
_STRATEGY_TYPE_MAP = {
    "trailing-stop": StrategyType.TRAILING_STOP,
    "bracket": StrategyType.BRACKET,
    "scale-out": StrategyType.SCALE_OUT,
    "grid": StrategyType.GRID,
}


def list_strategies() -> StrategyListResponse:
    """List all configured strategies.

    Returns:
        List of strategy response schemas.
    """
    strategies = load_strategies()
    return StrategyListResponse(
        strategies=[StrategyResponse.from_domain(s) for s in strategies],
        count=len(strategies),
    )


def get_strategy_detail(strategy_id: str) -> StrategyResponse:
    """Get detailed info for a strategy.

    Args:
        strategy_id: Strategy ID.

    Returns:
        Strategy response schema.

    Raises:
        NotFoundError: If strategy not found.
    """
    strat = _get_strategy(strategy_id)
    if strat is None:
        raise NotFoundError(
            message=f"Strategy {strategy_id} not found",
            code="STRATEGY_NOT_FOUND",
        )
    return StrategyResponse.from_domain(strat)


def create_strategy(config: Config, request: StrategyCreate) -> StrategyResponse:
    """Create and save a new strategy.

    Args:
        config: Application configuration (needed for grid strategies).
        request: Strategy creation request.

    Returns:
        Created strategy response.

    Raises:
        ValidationError: If strategy parameters are invalid.
        ConfigurationError: If broker access is needed but not configured.
    """
    strat_type = _STRATEGY_TYPE_MAP.get(request.strategy_type)
    if strat_type is None:
        raise ValidationError(
            message=f"Unknown strategy type: {request.strategy_type}",
            code="INVALID_STRATEGY_TYPE",
            suggestion=f"Valid types: {', '.join(_STRATEGY_TYPE_MAP.keys())}",
        )

    defaults = config.strategy_defaults
    entry_type = EntryType.LIMIT if request.entry_price else EntryType.MARKET
    entry_price = Decimal(str(request.entry_price)) if request.entry_price else None

    try:
        if strat_type == StrategyType.TRAILING_STOP:
            trailing = (
                _to_pct(Decimal(str(request.trailing_pct)))
                if request.trailing_pct
                else defaults.trailing_stop_pct
            )
            strat = Strategy(
                symbol=request.symbol.upper(),
                strategy_type=strat_type,
                quantity=request.qty,
                entry_type=entry_type,
                entry_price=entry_price,
                trailing_stop_pct=trailing,
            )

        elif strat_type == StrategyType.BRACKET:
            tp = (
                _to_pct(Decimal(str(request.take_profit)))
                if request.take_profit
                else defaults.take_profit_pct
            )
            sl = (
                _to_pct(Decimal(str(request.stop_loss)))
                if request.stop_loss
                else defaults.stop_loss_pct
            )
            strat = Strategy(
                symbol=request.symbol.upper(),
                strategy_type=strat_type,
                quantity=request.qty,
                entry_type=entry_type,
                entry_price=entry_price,
                take_profit_pct=tp,
                stop_loss_pct=sl,
            )

        elif strat_type == StrategyType.SCALE_OUT:
            strat = Strategy(
                symbol=request.symbol.upper(),
                strategy_type=strat_type,
                quantity=request.qty,
                entry_type=entry_type,
                entry_price=entry_price,
                scale_targets=defaults.scale_tranches,
            )

        elif strat_type == StrategyType.GRID:
            from trader.app import get_broker

            broker = get_broker(config)
            quote = broker.get_quote(request.symbol.upper())
            mid_price = (quote.bid + quote.ask) / 2

            grid_levels = request.levels or defaults.grid_levels
            spacing = defaults.grid_spacing_pct

            low = mid_price * (1 - (spacing * grid_levels) / 100)
            high = mid_price * (1 + (spacing * grid_levels) / 100)

            strat = Strategy(
                symbol=request.symbol.upper(),
                strategy_type=strat_type,
                quantity=request.qty,
                grid_config={
                    "low": float(low),
                    "high": float(high),
                    "levels": grid_levels,
                    "qty_per_level": defaults.grid_qty_per_level,
                },
            )
        else:
            raise ValidationError(
                message=f"Unknown strategy type: {request.strategy_type}",
                code="INVALID_STRATEGY_TYPE",
            )

    except ValueError as e:
        raise ValidationError(
            message=str(e),
            code="INVALID_STRATEGY_PARAMS",
        )

    _save_strategy(strat)
    audit_log(
        "create_strategy",
        {"strategy_type": request.strategy_type, "symbol": strat.symbol, "strategy_id": strat.id},
        log_dir=config.log_dir,
    )
    return StrategyResponse.from_domain(strat)


def remove_strategy(strategy_id: str) -> dict[str, str]:
    """Remove a strategy.

    Args:
        strategy_id: Strategy ID to remove.

    Returns:
        Dict with status message.

    Raises:
        NotFoundError: If strategy not found.
    """
    if not _delete_strategy(strategy_id):
        raise NotFoundError(
            message=f"Strategy {strategy_id} not found",
            code="STRATEGY_NOT_FOUND",
        )
    from trader.utils.config import load_config

    audit_log("remove_strategy", {"strategy_id": strategy_id}, log_dir=load_config().log_dir)
    return {"status": "removed", "strategy_id": strategy_id}


def set_strategy_enabled(strategy_id: str, enabled: bool) -> dict[str, str]:
    """Enable or disable a strategy.

    Args:
        strategy_id: Strategy ID.
        enabled: Whether to enable or disable.

    Returns:
        Dict with status message.

    Raises:
        NotFoundError: If strategy not found.
    """
    if not _enable_strategy(strategy_id, enabled=enabled):
        raise NotFoundError(
            message=f"Strategy {strategy_id} not found",
            code="STRATEGY_NOT_FOUND",
        )
    action = "enabled" if enabled else "disabled"
    return {"status": action, "strategy_id": strategy_id}


def pause_strategy(strategy_id: str) -> dict[str, str]:
    """Pause an active strategy.

    Args:
        strategy_id: Strategy ID.

    Returns:
        Dict with status message.

    Raises:
        NotFoundError: If strategy not found.
        ValidationError: If strategy is already in a terminal state.
    """
    strat = _get_strategy(strategy_id)
    if strat is None:
        raise NotFoundError(
            message=f"Strategy {strategy_id} not found",
            code="STRATEGY_NOT_FOUND",
        )

    if strat.is_terminal():
        raise ValidationError(
            message=f"Strategy is already {strat.phase.value}",
            code="STRATEGY_TERMINAL",
        )

    strat.update_phase(StrategyPhase.PAUSED)
    _save_strategy(strat)
    return {"status": "paused", "strategy_id": strategy_id}


def resume_strategy(strategy_id: str) -> dict[str, str]:
    """Resume a paused strategy.

    Args:
        strategy_id: Strategy ID.

    Returns:
        Dict with status message.

    Raises:
        NotFoundError: If strategy not found.
        ValidationError: If strategy is not paused.
    """
    strat = _get_strategy(strategy_id)
    if strat is None:
        raise NotFoundError(
            message=f"Strategy {strategy_id} not found",
            code="STRATEGY_NOT_FOUND",
        )

    if strat.phase != StrategyPhase.PAUSED:
        raise ValidationError(
            message=f"Strategy is not paused (current: {strat.phase.value})",
            code="STRATEGY_NOT_PAUSED",
        )

    if strat.entry_fill_price:
        strat.update_phase(StrategyPhase.POSITION_OPEN)
    else:
        strat.update_phase(StrategyPhase.PENDING)

    _save_strategy(strat)
    return {"status": "resumed", "strategy_id": strategy_id, "phase": strat.phase.value}
