"""Integration helpers for pandas-ta."""

from __future__ import annotations

from typing import Any


def get_pandas_ta() -> Any:
    """Return pandas-ta module if installed, otherwise None."""
    try:
        import pandas_ta as ta
    except ImportError:
        return None

    return ta
