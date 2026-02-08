"""Base indicator abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class IndicatorSpec:
    """Metadata describing an indicator."""

    name: str
    description: str
    params: dict[str, str] = field(default_factory=dict)
    output: str = ""


class Indicator(ABC):
    """Base class for technical indicators."""

    @property
    @abstractmethod
    def spec(self) -> IndicatorSpec:
        """Indicator metadata."""

    @abstractmethod
    def calculate(self, data: pd.DataFrame):
        """Calculate the indicator from OHLCV data."""


def validate_ohlcv(data: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
