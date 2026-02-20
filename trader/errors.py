"""Shared error types for BareTrader.

All application-level errors inherit from AppError. Each error carries:
- message: Human-readable description
- code: Machine-readable error code (e.g., "API_KEY_MISSING")
- details: Optional dict with additional context
- suggestion: Optional hint for how to resolve the error

Both CLI and MCP interfaces handle these errors uniformly.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base error for all application-level errors."""

    def __init__(
        self,
        message: str,
        code: str,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        self.suggestion = suggestion
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize error for JSON output."""
        result: dict[str, Any] = {
            "error": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class ValidationError(AppError):
    """Input validation failed (bad parameters, missing required fields)."""

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class NotFoundError(AppError):
    """Resource not found (strategy, backtest, order, indicator)."""

    def __init__(
        self,
        message: str,
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class ConfigurationError(AppError):
    """Missing or invalid configuration (API keys, data sources)."""

    def __init__(
        self,
        message: str,
        code: str = "CONFIGURATION_ERROR",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class BrokerError(AppError):
    """Error communicating with broker."""

    def __init__(
        self,
        message: str,
        code: str = "BROKER_ERROR",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class SafetyError(AppError):
    """Order blocked by safety checks."""

    def __init__(
        self,
        message: str,
        code: str = "SAFETY_BLOCKED",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class EngineError(AppError):
    """Engine state error (already running, not running, etc.)."""

    def __init__(
        self,
        message: str,
        code: str = "ENGINE_ERROR",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class RateLimitError(AppError):
    """Request rejected due to rate limit (e.g. too many long-running tasks)."""

    def __init__(
        self,
        message: str,
        code: str = "RATE_LIMIT_EXCEEDED",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)


class TaskTimeoutError(AppError):
    """Long-running task was aborted because it exceeded the allowed time."""

    def __init__(
        self,
        message: str,
        code: str = "TASK_TIMEOUT",
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, code, details, suggestion)
