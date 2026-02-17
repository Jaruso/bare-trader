"""Engine status and control service functions."""

from __future__ import annotations

import os
import signal

from trader.errors import EngineError
from trader.schemas.engine import EngineStatus
from trader.utils.config import Config


def get_engine_status(config: Config) -> EngineStatus:
    """Get current engine status.

    Args:
        config: Application configuration.

    Returns:
        Engine status schema.
    """
    from trader.core.engine import get_lock_file_path
    from trader.strategies.loader import load_strategies

    lock_path = get_lock_file_path()
    running = False
    pid = None

    if lock_path.exists():
        try:
            with open(lock_path) as f:
                pid_str = f.read().strip()
                if pid_str:
                    candidate_pid = int(pid_str)
                    try:
                        os.kill(candidate_pid, 0)
                        running = True
                        pid = candidate_pid
                    except ProcessLookupError:
                        pass  # Stale lock file
        except (ValueError, FileNotFoundError):
            pass

    has_key = bool(config.alpaca_api_key)

    # Count active strategies
    try:
        strategies = load_strategies()
        active_count = sum(1 for s in strategies if s.enabled and s.is_active())
    except Exception:
        active_count = 0

    # Build contextual hint for agents
    hint = None
    if not has_key:
        hint = "API key not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
    elif not running and active_count == 0:
        hint = "Engine not running because no active strategies are configured. Add a strategy first with create_strategy, then start the engine."
    elif not running:
        hint = "Engine not running. Start it with the CLI: trader start"

    return EngineStatus(
        running=running,
        pid=pid,
        environment=config.env.value.upper(),
        service=config.service.value,
        base_url=config.base_url,
        api_key_configured=has_key,
        active_strategies=active_count,
        hint=hint,
    )


def start_engine(dry_run: bool = False, interval: int = 60) -> dict[str, str]:
    """Start the trading engine as a background process.

    Spawns `trader start` as a detached subprocess so the call returns
    immediately. The engine writes its PID to the lock file; subsequent
    calls to get_engine_status will show it as running.

    Args:
        dry_run:  If True, evaluate strategies but do not execute trades.
        interval: Poll interval in seconds (default 60).

    Returns:
        Dict with status and pid of the launched process.

    Raises:
        EngineError: If the engine is already running or cannot be started.
    """
    import subprocess
    import sys
    import time

    from trader.core.engine import get_lock_file_path

    # Refuse if already running.
    lock_path = get_lock_file_path()
    if lock_path.exists():
        try:
            with open(lock_path) as f:
                pid_str = f.read().strip()
            if pid_str:
                try:
                    os.kill(int(pid_str), 0)
                    raise EngineError(
                        message=f"Engine is already running (PID {pid_str})",
                        code="ENGINE_ALREADY_RUNNING",
                        details={"pid": int(pid_str)},
                        suggestion="Use stop_engine first, or force-start via CLI with --force",
                    )
                except ProcessLookupError:
                    lock_path.unlink()  # stale lock — clean up and continue
        except (ValueError, FileNotFoundError):
            pass

    # Build the command: use the same Python interpreter so venv is respected.
    cmd = [sys.executable, "-m", "trader.cli.main", "start",
           f"--interval={interval}"]
    if dry_run:
        cmd.append("--dry-run")

    # Spawn detached (no controlling terminal, stdout/stderr to /dev/null).
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Give the engine a moment to write its lock file before returning.
    time.sleep(1.5)

    from trader.audit import log_action as audit_log
    from trader.utils.config import load_config

    audit_log(
        "start_engine",
        {"pid": proc.pid, "dry_run": dry_run, "interval": interval},
        log_dir=load_config().log_dir,
    )

    return {
        "status": "started",
        "pid": str(proc.pid),
        "mode": "dry_run" if dry_run else "live",
        "interval": str(interval),
    }


def stop_engine(force: bool = False) -> dict[str, str]:
    """Stop the running trading engine.

    Args:
        force: If True, send SIGKILL instead of SIGTERM.

    Returns:
        Dict with status message.

    Raises:
        EngineError: If engine is not running or cannot be stopped.
    """
    from trader.core.engine import get_lock_file_path

    lock_path = get_lock_file_path()

    if not lock_path.exists():
        raise EngineError(
            message="No trading engine is currently running",
            code="ENGINE_NOT_RUNNING",
        )

    # Read PID
    try:
        with open(lock_path) as f:
            pid_str = f.read().strip()
            if not pid_str:
                lock_path.unlink()
                raise EngineError(
                    message="Lock file is empty - no engine running",
                    code="ENGINE_NOT_RUNNING",
                )
            pid = int(pid_str)
    except (ValueError, FileNotFoundError) as e:
        raise EngineError(
            message=f"Error reading lock file: {e}",
            code="ENGINE_LOCK_ERROR",
        )

    # Check if process exists
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        try:
            lock_path.unlink()
        except Exception:
            pass
        raise EngineError(
            message=f"Engine process (PID {pid}) is not running",
            code="ENGINE_NOT_RUNNING",
            details={"pid": pid, "stale_lock": True},
            suggestion="Stale lock file was cleaned up",
        )
    except PermissionError:
        raise EngineError(
            message=f"Permission denied to signal process {pid}",
            code="ENGINE_PERMISSION_DENIED",
        )

    # Send signal
    sig = signal.SIGKILL if force else signal.SIGTERM

    try:
        os.kill(pid, sig)
        from trader.audit import log_action as audit_log
        from trader.utils.config import load_config

        audit_log(
            "stop_engine",
            {"pid": pid, "force": force},
            log_dir=load_config().log_dir,
        )
        if force:
            try:
                lock_path.unlink()
            except Exception:
                pass
            return {"status": "killed", "pid": str(pid)}
        else:
            return {"status": "stopping", "pid": str(pid)}
    except ProcessLookupError:
        return {"status": "already_stopped", "pid": str(pid)}
    except PermissionError:
        raise EngineError(
            message=f"Permission denied to stop process {pid}",
            code="ENGINE_PERMISSION_DENIED",
        )
