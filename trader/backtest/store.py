"""Storage and retrieval of backtest results."""

import json
from pathlib import Path
from typing import Optional

from trader.backtest.results import BacktestResult


def get_backtests_dir(data_dir: Optional[Path] = None) -> Path:
    """Get the backtests directory, creating if needed.

    Args:
        data_dir: Base data directory (defaults to ./data).

    Returns:
        Path to backtests directory.
    """
    if data_dir is None:
        data_dir = Path.cwd() / "data"

    backtests_dir = data_dir / "backtests"
    backtests_dir.mkdir(parents=True, exist_ok=True)
    return backtests_dir


def save_backtest(result: BacktestResult, data_dir: Optional[Path] = None) -> None:
    """Save backtest result to JSON.

    Saves to data/backtests/{id}.json and updates index.

    Args:
        result: BacktestResult to save.
        data_dir: Base data directory (defaults to ./data).
    """
    backtests_dir = get_backtests_dir(data_dir)

    # Save full result
    result_file = backtests_dir / f"{result.id}.json"
    with open(result_file, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    # Update index
    _update_index(result, backtests_dir)


def load_backtest(
    backtest_id: str, data_dir: Optional[Path] = None
) -> BacktestResult:
    """Load backtest result from JSON.

    Args:
        backtest_id: Backtest ID to load.
        data_dir: Base data directory (defaults to ./data).

    Returns:
        BacktestResult.

    Raises:
        FileNotFoundError: If backtest not found.
    """
    backtests_dir = get_backtests_dir(data_dir)
    result_file = backtests_dir / f"{backtest_id}.json"

    if not result_file.exists():
        raise FileNotFoundError(f"Backtest {backtest_id} not found at {result_file}")

    with open(result_file, "r") as f:
        data = json.load(f)

    return BacktestResult.from_dict(data)


def list_backtests(data_dir: Optional[Path] = None) -> list[dict]:
    """List all backtest results (metadata only).

    Args:
        data_dir: Base data directory (defaults to ./data).

    Returns:
        List of backtest metadata dicts.
    """
    backtests_dir = get_backtests_dir(data_dir)
    index_file = backtests_dir / "index.json"

    if not index_file.exists():
        return []

    with open(index_file, "r") as f:
        index = json.load(f)

    return index.get("backtests", [])


def delete_backtest(backtest_id: str, data_dir: Optional[Path] = None) -> bool:
    """Delete a backtest result.

    Args:
        backtest_id: Backtest ID to delete.
        data_dir: Base data directory (defaults to ./data).

    Returns:
        True if deleted, False if not found.
    """
    backtests_dir = get_backtests_dir(data_dir)
    result_file = backtests_dir / f"{backtest_id}.json"

    if not result_file.exists():
        return False

    # Delete file
    result_file.unlink()

    # Update index
    _remove_from_index(backtest_id, backtests_dir)

    return True


def _update_index(result: BacktestResult, backtests_dir: Path) -> None:
    """Update the index file with backtest metadata.

    Args:
        result: BacktestResult to add to index.
        backtests_dir: Directory containing backtests.
    """
    index_file = backtests_dir / "index.json"

    # Load existing index
    if index_file.exists():
        with open(index_file, "r") as f:
            index = json.load(f)
    else:
        index = {"backtests": []}

    # Remove existing entry if updating
    index["backtests"] = [b for b in index["backtests"] if b["id"] != result.id]

    # Add new entry
    metadata = {
        "id": result.id,
        "strategy_type": result.strategy_type,
        "symbol": result.symbol,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "created_at": result.created_at.isoformat(),
        "total_return_pct": str(result.total_return_pct),
        "win_rate": str(result.win_rate),
        "total_trades": result.total_trades,
        "max_drawdown_pct": str(result.max_drawdown_pct),
    }

    index["backtests"].append(metadata)

    # Sort by created_at (most recent first)
    index["backtests"].sort(
        key=lambda x: x["created_at"], reverse=True
    )

    # Save index
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)


def _remove_from_index(backtest_id: str, backtests_dir: Path) -> None:
    """Remove a backtest from the index.

    Args:
        backtest_id: Backtest ID to remove.
        backtests_dir: Directory containing backtests.
    """
    index_file = backtests_dir / "index.json"

    if not index_file.exists():
        return

    with open(index_file, "r") as f:
        index = json.load(f)

    # Remove entry
    index["backtests"] = [b for b in index["backtests"] if b["id"] != backtest_id]

    # Save index
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)
