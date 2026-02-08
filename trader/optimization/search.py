"""Search algorithms for parameter optimization."""

from __future__ import annotations

import itertools
import random
from typing import Any


def generate_grid(param_grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Generate all combinations from a parameter grid."""
    if not param_grid:
        return []

    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]
    combos = []
    for combo in itertools.product(*values):
        combos.append(dict(zip(keys, combo, strict=False)))
    return combos


def generate_random(
    param_grid: dict[str, list[Any]], num_samples: int, seed: int | None = None
) -> list[dict[str, Any]]:
    """Randomly sample parameter combinations."""
    if not param_grid:
        return []

    if seed is not None:
        random.seed(seed)

    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]
    samples = []
    for _ in range(num_samples):
        choice = [random.choice(options) for options in values]
        samples.append(dict(zip(keys, choice, strict=False)))
    return samples
