"""Central audit log for CLI and MCP actions.

Phase 3 (MCP roadmap): log sensitive operations from both interfaces
so we have an immutable trail for compliance and debugging.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_audit_source: ContextVar[str] = ContextVar("audit_source", default="cli")


def set_audit_source(source: str) -> None:
    """Set the current audit source (e.g. 'cli' or 'mcp') for this context."""
    _audit_source.set(source)


def get_audit_source() -> str:
    """Return the current audit source."""
    return _audit_source.get()


def log_action(
    action: str,
    details: dict[str, Any],
    *,
    error: str | None = None,
    log_dir: Path | None = None,
) -> None:
    """Append one audit record to the audit log.

    Args:
        action: Action name (e.g. 'place_order', 'create_strategy', 'stop_engine').
        details: Structured details (symbol, qty, order_id, etc.). Keep small; no secrets.
        error: If the action failed, a short error message.
        log_dir: Directory for audit.log. If None, no write (caller should pass config.log_dir).
    """
    if log_dir is None:
        return
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audit.log"
    record = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "source": get_audit_source(),
        "action": action,
        "details": details,
    }
    if error is not None:
        record["error"] = error
    line = json.dumps(record, default=str) + "\n"
    try:
        with open(log_file, "a") as f:
            f.write(line)
    except OSError:
        pass  # Don't fail the request if audit write fails
