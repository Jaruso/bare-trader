"""Manage system cron job for scheduled trading cycles (trader run-once).

Used by `trader schedule enable` and `trader schedule disable`.
Only supported on Unix-like systems (macOS, Linux).
"""

from __future__ import annotations

import os
import shutil
import subprocess

# Comment at end of our crontab line so we can find and remove it
AUTOTRADER_MARKER = "# AutoTrader schedule"


def _is_unix() -> bool:
    return os.name == "posix"


def get_trader_path() -> str | None:
    """Return full path to 'trader' executable, or None if not on PATH."""
    return shutil.which("trader")


def get_current_crontab() -> list[str]:
    """Return current crontab lines (empty list if no crontab or error)."""
    if not _is_unix():
        return []
    try:
        out = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout:
            return [line.rstrip() for line in out.stdout.rstrip().split("\n")]
        # Exit 1 often means "no crontab"; treat as empty
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _build_cron_line(trader_path: str, every_minutes: int) -> str:
    """Build the single crontab line we install."""
    if every_minutes <= 0 or every_minutes > 60:
        raise ValueError("every_minutes must be between 1 and 60")
    if every_minutes == 1:
        spec = "* * * * *"
    else:
        spec = f"*/{every_minutes} * * * *"
    return f"{spec} {trader_path} run-once   {AUTOTRADER_MARKER}"


def _is_our_line(line: str) -> bool:
    return AUTOTRADER_MARKER in line and "run-once" in line


def is_schedule_enabled() -> bool:
    """Return True if the AutoTrader cron job is present."""
    lines = get_current_crontab()
    return any(_is_our_line(line) for line in lines)


def get_schedule_status() -> dict:
    """Return status dict: enabled, line (if enabled), trader_path, supported."""
    supported = _is_unix()
    trader_path = get_trader_path() if supported else None
    lines = get_current_crontab() if supported else []
    our_lines = [line for line in lines if _is_our_line(line)]
    enabled = len(our_lines) > 0
    return {
        "enabled": enabled,
        "line": our_lines[0] if our_lines else None,
        "trader_path": trader_path,
        "supported": supported,
    }


def enable_schedule(every_minutes: int = 5) -> None:
    """Add a cron job that runs 'trader run-once' every every_minutes minutes.

    Raises:
        RuntimeError: If not on Unix or 'trader' not on PATH.
        ValueError: If every_minutes not in 1..60.
    """
    if not _is_unix():
        raise RuntimeError("Schedule (cron) is only supported on macOS and Linux.")
    path = get_trader_path()
    if not path:
        raise RuntimeError(
            "'trader' not found on PATH. Install with pipx or ensure the trader binary is on PATH."
        )
    if every_minutes < 1 or every_minutes > 60:
        raise ValueError("--every must be between 1 and 60 (minutes).")

    new_line = _build_cron_line(path, every_minutes)
    lines = get_current_crontab()
    # Remove any existing AutoTrader line so we don't duplicate
    lines = [line for line in lines if not _is_our_line(line)]
    lines.append(new_line)
    new_crontab = "\n".join(lines) + "\n"
    try:
        result = subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("crontab command timed out.")
    if result.returncode != 0:
        raise RuntimeError("Failed to install crontab (crontab - returned non-zero).")


def disable_schedule() -> None:
    """Remove the AutoTrader cron job if present.

    Raises:
        RuntimeError: If not on Unix.
    """
    if not _is_unix():
        raise RuntimeError("Schedule (cron) is only supported on macOS and Linux.")
    lines = get_current_crontab()
    new_lines = [line for line in lines if not _is_our_line(line)]
    if not new_lines:
        # No other lines; remove crontab entirely
        try:
            subprocess.run(["crontab", "-r"], capture_output=True, timeout=5)
        except FileNotFoundError:
            pass
        return
    new_crontab = "\n".join(new_lines) + "\n"
    try:
        subprocess.run(["crontab", "-"], input=new_crontab, capture_output=True, text=True, timeout=5)
    except FileNotFoundError:
        raise RuntimeError("crontab command not found.")
