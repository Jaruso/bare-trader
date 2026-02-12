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
