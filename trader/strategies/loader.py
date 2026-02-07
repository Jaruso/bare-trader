"""Strategy loading and persistence.

Strategies are stored in YAML format at config/strategies.yaml.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from trader.strategies.models import Strategy


def get_strategies_file(config_dir: Optional[Path] = None) -> Path:
    """Get path to strategies file."""
    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "strategies.yaml"


def load_strategies(config_dir: Optional[Path] = None) -> list[Strategy]:
    """Load all strategies from YAML file.

    Args:
        config_dir: Config directory path.

    Returns:
        List of Strategy objects.
    """
    strategies_file = get_strategies_file(config_dir)

    if not strategies_file.exists():
        return []

    with open(strategies_file) as f:
        data = yaml.safe_load(f)

    if not data or "strategies" not in data:
        return []

    return [Strategy.from_dict(s) for s in data["strategies"]]


def save_strategies(strategies: list[Strategy], config_dir: Optional[Path] = None) -> None:
    """Save all strategies to YAML file.

    Args:
        strategies: List of strategies to save.
        config_dir: Config directory path.
    """
    strategies_file = get_strategies_file(config_dir)

    data = {"strategies": [s.to_dict() for s in strategies]}

    with open(strategies_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def save_strategy(strategy: Strategy, config_dir: Optional[Path] = None) -> None:
    """Add or update a single strategy.

    Args:
        strategy: Strategy to save.
        config_dir: Config directory path.
    """
    strategies = load_strategies(config_dir)

    # Check if strategy with same ID exists
    existing_idx = None
    for i, s in enumerate(strategies):
        if s.id == strategy.id:
            existing_idx = i
            break

    # Update timestamp
    strategy.updated_at = datetime.now()

    if existing_idx is not None:
        strategies[existing_idx] = strategy
    else:
        strategies.append(strategy)

    save_strategies(strategies, config_dir)


def delete_strategy(strategy_id: str, config_dir: Optional[Path] = None) -> bool:
    """Delete a strategy by ID.

    Args:
        strategy_id: Strategy ID to delete.
        config_dir: Config directory path.

    Returns:
        True if strategy was deleted, False if not found.
    """
    strategies = load_strategies(config_dir)
    original_count = len(strategies)

    strategies = [s for s in strategies if s.id != strategy_id]

    if len(strategies) == original_count:
        return False

    save_strategies(strategies, config_dir)
    return True


def get_strategy(strategy_id: str, config_dir: Optional[Path] = None) -> Optional[Strategy]:
    """Get a strategy by ID.

    Args:
        strategy_id: Strategy ID to find.
        config_dir: Config directory path.

    Returns:
        Strategy if found, None otherwise.
    """
    strategies = load_strategies(config_dir)
    for s in strategies:
        if s.id == strategy_id:
            return s
    return None


def enable_strategy(strategy_id: str, enabled: bool = True, config_dir: Optional[Path] = None) -> bool:
    """Enable or disable a strategy.

    Args:
        strategy_id: Strategy ID.
        enabled: Whether to enable or disable.
        config_dir: Config directory path.

    Returns:
        True if strategy was updated, False if not found.
    """
    strategy = get_strategy(strategy_id, config_dir)
    if strategy is None:
        return False

    strategy.enabled = enabled
    save_strategy(strategy, config_dir)
    return True


def get_active_strategies(config_dir: Optional[Path] = None) -> list[Strategy]:
    """Get all active (non-terminal, enabled) strategies.

    Args:
        config_dir: Config directory path.

    Returns:
        List of active strategies.
    """
    strategies = load_strategies(config_dir)
    return [s for s in strategies if s.enabled and s.is_active()]
