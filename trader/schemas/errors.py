"""Error response schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from baretrader.errors import AppError


class ErrorResponse(BaseModel):
    """Structured error response for JSON output."""

    error: str
    message: str
    details: dict[str, Any] = {}
    suggestion: str | None = None

    @classmethod
    def from_error(cls, error: AppError) -> ErrorResponse:
        """Create from an AppError instance."""
        return cls(
            error=error.code,
            message=error.message,
            details=error.details,
            suggestion=error.suggestion,
        )
