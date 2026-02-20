"""Indicator schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from baretrader.indicators.base import IndicatorSpec


class IndicatorInfo(BaseModel):
    """Indicator metadata."""

    name: str
    description: str
    params: dict[str, str]
    output: str

    @classmethod
    def from_domain(cls, spec: IndicatorSpec) -> IndicatorInfo:
        return cls(
            name=spec.name,
            description=spec.description,
            params=spec.params,
            output=spec.output,
        )
