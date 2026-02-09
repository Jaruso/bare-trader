"""Shared types used across schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """A date range for filtering."""

    start: datetime
    end: datetime


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)
