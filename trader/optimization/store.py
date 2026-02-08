"""Storage and retrieval of optimization results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from trader.optimization.results import OptimizationResult


def get_optimizations_dir(data_dir: Optional[Path] = None) -> Path:
    """Get the optimizations directory, creating if needed."""
    if data_dir is None:
        data_dir = Path.cwd() / "data"

    optimizations_dir = data_dir / "optimizations"
    optimizations_dir.mkdir(parents=True, exist_ok=True)
    return optimizations_dir


def save_optimization(result: OptimizationResult, data_dir: Optional[Path] = None) -> None:
    """Save optimization result to JSON and update index."""
    optimizations_dir = get_optimizations_dir(data_dir)
    result_file = optimizations_dir / f"{result.id}.json"
    with open(result_file, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    _update_index(result, optimizations_dir)


def load_optimization(
    optimization_id: str, data_dir: Optional[Path] = None
) -> OptimizationResult:
    """Load an optimization result from JSON."""
    optimizations_dir = get_optimizations_dir(data_dir)
    result_file = optimizations_dir / f"{optimization_id}.json"

    if not result_file.exists():
        raise FileNotFoundError(
            f"Optimization {optimization_id} not found at {result_file}"
        )

    with open(result_file, "r") as f:
        data = json.load(f)

    return OptimizationResult.from_dict(data)


def list_optimizations(data_dir: Optional[Path] = None) -> list[dict]:
    """List all optimization results (metadata only)."""
    optimizations_dir = get_optimizations_dir(data_dir)
    index_file = optimizations_dir / "index.json"

    if not index_file.exists():
        return []

    with open(index_file, "r") as f:
        index = json.load(f)

    return index.get("optimizations", [])


def delete_optimization(optimization_id: str, data_dir: Optional[Path] = None) -> bool:
    """Delete an optimization result."""
    optimizations_dir = get_optimizations_dir(data_dir)
    result_file = optimizations_dir / f"{optimization_id}.json"

    if not result_file.exists():
        return False

    result_file.unlink()
    _remove_from_index(optimization_id, optimizations_dir)
    return True


def _update_index(result: OptimizationResult, optimizations_dir: Path) -> None:
    index_file = optimizations_dir / "index.json"

    if index_file.exists():
        with open(index_file, "r") as f:
            index = json.load(f)
    else:
        index = {"optimizations": []}

    index["optimizations"] = [
        entry for entry in index["optimizations"] if entry["id"] != result.id
    ]

    metadata = {
        "id": result.id,
        "strategy_type": result.strategy_type,
        "symbol": result.symbol,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "created_at": result.created_at.isoformat(),
        "objective": result.objective,
        "method": result.method,
        "best_score": str(result.best_score),
        "num_combinations": result.num_combinations,
    }

    index["optimizations"].append(metadata)
    index["optimizations"].sort(key=lambda x: x["created_at"], reverse=True)

    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)


def _remove_from_index(optimization_id: str, optimizations_dir: Path) -> None:
    index_file = optimizations_dir / "index.json"
    if not index_file.exists():
        return

    with open(index_file, "r") as f:
        index = json.load(f)

    index["optimizations"] = [
        entry for entry in index["optimizations"] if entry["id"] != optimization_id
    ]

    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)
