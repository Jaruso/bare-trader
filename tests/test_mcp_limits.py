"""Tests for MCP rate limits and timeouts."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from baretrader.errors import RateLimitError, TaskTimeoutError
from baretrader.mcp import limits as limits_mod


# Reset rate limit state between tests so env-driven limits don't leak
def _clear_rate_limit_state() -> None:
    with limits_mod._rate_limit_lock:
        limits_mod._rate_limit_entries.clear()


class TestRateLimiter:
    """Test check_rate_limit behavior."""

    def test_no_limit_when_env_zero(self) -> None:
        _clear_rate_limit_state()
        with patch.dict("os.environ", {"MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE": "0"}, clear=False):
            limits_mod.check_rate_limit("no_limit_key")
            limits_mod.check_rate_limit("no_limit_key")
            limits_mod.check_rate_limit("no_limit_key")

    def test_allows_up_to_limit(self) -> None:
        _clear_rate_limit_state()
        with patch.dict("os.environ", {"MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE": "2"}, clear=False):
            limits_mod.check_rate_limit("allow_key")
            limits_mod.check_rate_limit("allow_key")

    def test_raises_after_limit_exceeded(self) -> None:
        _clear_rate_limit_state()
        with patch.dict("os.environ", {"MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE": "2"}, clear=False):
            limits_mod.check_rate_limit("exceed_key")
            limits_mod.check_rate_limit("exceed_key")
            with pytest.raises(RateLimitError) as exc_info:
                limits_mod.check_rate_limit("exceed_key")
        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"
        assert "exceed_key" in exc_info.value.message
        assert "2" in exc_info.value.message

    def test_different_keys_are_independent(self) -> None:
        _clear_rate_limit_state()
        with patch.dict("os.environ", {"MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE": "2"}, clear=False):
            limits_mod.check_rate_limit("key_a")
            limits_mod.check_rate_limit("key_b")
            limits_mod.check_rate_limit("key_a")
            limits_mod.check_rate_limit("key_b")
            with pytest.raises(RateLimitError):
                limits_mod.check_rate_limit("key_a")
            with pytest.raises(RateLimitError):
                limits_mod.check_rate_limit("key_b")


class TestTimeoutRunner:
    """Test run_with_timeout."""

    def test_returns_result_when_completes_in_time(self) -> None:
        result = limits_mod.run_with_timeout(lambda: 42, timeout_seconds=5, task_name="quick")
        assert result == 42

    def test_raises_task_timeout_when_exceeds_time(self) -> None:
        def slow() -> int:
            time.sleep(2)
            return 1

        with pytest.raises(TaskTimeoutError) as exc_info:
            limits_mod.run_with_timeout(slow, timeout_seconds=1, task_name="slow_task")
        assert exc_info.value.code == "TASK_TIMEOUT"
        assert "slow_task" in exc_info.value.message
        assert "1" in exc_info.value.message

    def test_zero_timeout_runs_in_caller_thread(self) -> None:
        result = limits_mod.run_with_timeout(lambda: 99, timeout_seconds=0, task_name="no_timeout")
        assert result == 99

    def test_negative_timeout_runs_in_caller_thread(self) -> None:
        result = limits_mod.run_with_timeout(
            lambda: 77, timeout_seconds=-1, task_name="negative"
        )
        assert result == 77

    def test_propagates_other_exceptions(self) -> None:
        def fail() -> None:
            raise ValueError("oops")

        with pytest.raises(ValueError, match="oops"):
            limits_mod.run_with_timeout(fail, timeout_seconds=5, task_name="fail")


class TestConfigGetters:
    """Test env-based config getters."""

    def test_backtest_timeout_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert limits_mod.get_backtest_timeout_seconds() == 300

    def test_backtest_timeout_from_env(self) -> None:
        with patch.dict("os.environ", {"MCP_BACKTEST_TIMEOUT_SECONDS": "120"}, clear=False):
            assert limits_mod.get_backtest_timeout_seconds() == 120

    def test_optimization_timeout_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert limits_mod.get_optimization_timeout_seconds() == 600

    def test_optimization_timeout_from_env(self) -> None:
        with patch.dict("os.environ", {"MCP_OPTIMIZATION_TIMEOUT_SECONDS": "900"}, clear=False):
            assert limits_mod.get_optimization_timeout_seconds() == 900

    def test_rate_limit_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert limits_mod.get_rate_limit_calls_per_minute() == 10

    def test_rate_limit_from_env(self) -> None:
        with patch.dict("os.environ", {"MCP_RATE_LIMIT_LONG_RUNNING_PER_MINUTE": "5"}, clear=False):
            assert limits_mod.get_rate_limit_calls_per_minute() == 5
