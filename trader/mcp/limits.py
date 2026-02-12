"""Rate limits and timeouts for MCP long-running tools.

Phase 3 (MCP roadmap): protect the server from runaway agents by
- limiting how often long-running tools (backtest, optimization) can be invoked
- enforcing a maximum wall-clock time per invocation

Configuration is via environment variables; see README for MCP_* env vars.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Callable, TypeVar

from trader.errors import RateLimitError, TaskTimeoutError

T = TypeVar("T")

# Defaults (overridable by env)
DEFAULT_BACKTEST_TIMEOUT_SECONDS = 300  # 5 minutes
DEFAULT_OPTIMIZATION_TIMEOUT_SECONDS = 600  # 10 minutes
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_RATE_LIMIT_CALLS_PER_WINDOW = 10  # max 10 long-running calls per minute

_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    """Lazy single-thread executor for running timed tasks."""
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp_task")
    return _executor


def get_backtest_timeout_seconds() -> int:
    """Backtest timeout in seconds (0 = no timeout)."""
    return int(os.getenv("MCP_BACKTEST_TIMEOUT_SECONDS", str(DEFAULT_BACKTEST_TIMEOUT_SECONDS)))


def get_optimization_timeout_seconds() -> int:
    """Optimization timeout in seconds (0 = no timeout)."""
    return int(os.getenv("MCP_OPTIMIZATION_TIMEOUT_SECONDS", str(DEFAULT_OPTIMIZATION_TIMEOUT_SECONDS)))


def get_rate_limit_calls_per_minute() -> int:
    """Max long-running tool calls per minute (0 = no limit)."""
    return int(os.getenv("MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE", str(DEFAULT_RATE_LIMIT_CALLS_PER_WINDOW)))


# -----------------------------------------------------------------------------
# Rate limiter (in-memory, per process)
# -----------------------------------------------------------------------------

_rate_limit_entries: dict[str, deque[float]] = {}
_rate_limit_lock = threading.Lock()


def check_rate_limit(key: str) -> None:
    """Raise RateLimitError if the key has exceeded the allowed calls per minute."""
    limit = get_rate_limit_calls_per_minute()
    if limit <= 0:
        return
    window = DEFAULT_RATE_LIMIT_WINDOW_SECONDS
    now = time.monotonic()
    with _rate_limit_lock:
        if key not in _rate_limit_entries:
            _rate_limit_entries[key] = deque(maxlen=limit + 64)
        q = _rate_limit_entries[key]
        # Drop timestamps outside the window
        while q and q[0] < now - window:
            q.popleft()
        if len(q) >= limit:
            raise RateLimitError(
                message=f"Rate limit exceeded for {key}: max {limit} calls per {window}s",
                code="RATE_LIMIT_EXCEEDED",
                details={"key": key, "limit": limit, "window_seconds": window},
                suggestion="Wait a minute before retrying or increase MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE",
            )
        q.append(now)


# -----------------------------------------------------------------------------
# Timeout runner
# -----------------------------------------------------------------------------


def run_with_timeout(
    fn: Callable[[], T],
    timeout_seconds: int,
    task_name: str = "task",
) -> T:
    """Run a callable in a thread and return its result, or raise TaskTimeoutError on timeout.

    If timeout is 0 or negative, the callable runs in the current thread with no timeout.
    """
    if timeout_seconds <= 0:
        return fn()

    executor = _get_executor()
    future: Future[T] = executor.submit(fn)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        raise TaskTimeoutError(
            message=f"{task_name} did not complete within {timeout_seconds}s",
            code="TASK_TIMEOUT",
            details={"task": task_name, "timeout_seconds": timeout_seconds},
            suggestion="Use a shorter date range or increase MCP_BACKTEST_TIMEOUT_SECONDS / MCP_OPTIMIZATION_TIMEOUT_SECONDS",
        )
