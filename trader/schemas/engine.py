"""Engine status schema."""

from __future__ import annotations

from pydantic import BaseModel


class EngineStatus(BaseModel):
    """Trading engine status."""

    running: bool
    pid: int | None = None
    environment: str
    service: str
    base_url: str
    api_key_configured: bool
    active_strategies: int = 0
    hint: str | None = None
