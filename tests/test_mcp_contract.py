"""MCP contract tests: validate each tool's response matches expected schema.

Success responses are validated against Pydantic schemas or minimal required keys.
Error responses are validated to have 'error' and 'message' (ErrorResponse shape).
Tools that require broker/API may return errors in CI; we still assert contract.
"""

from __future__ import annotations

import json
from typing import Any

from baretrader.schemas.engine import EngineStatus
from baretrader.schemas.errors import ErrorResponse
from baretrader.schemas.indicators import IndicatorInfo


def _parse(result: str) -> dict[str, Any] | list[Any]:
    """Parse MCP tool JSON response."""
    data = json.loads(result)
    return data


def _is_error(data: dict[str, Any]) -> bool:
    """True if response is an error payload."""
    return "error" in data and "message" in data


def _assert_error_contract(data: dict[str, Any]) -> None:
    """Validate error response matches ErrorResponse shape."""
    assert "error" in data, "Error response must have 'error'"
    assert "message" in data, "Error response must have 'message'"
    # Optional: validate with Pydantic
    ErrorResponse(
        error=data["error"],
        message=data["message"],
        details=data.get("details", {}),
        suggestion=data.get("suggestion"),
    )


# =============================================================================
# Engine
# =============================================================================


class TestContractGetStatus:
    """Contract: get_status returns EngineStatus or error."""

    def test_get_status_valid_json(self) -> None:
        from baretrader.mcp.server import get_status

        result = get_status()
        data = _parse(result)
        assert isinstance(data, dict)

    def test_get_status_success_schema(self) -> None:
        from baretrader.mcp.server import get_status

        result = get_status()
        data = _parse(result)
        if _is_error(data):
            _assert_error_contract(data)
            return
        EngineStatus.model_validate(data)

    def test_get_status_required_fields_when_success(self) -> None:
        from baretrader.mcp.server import get_status

        result = get_status()
        data = _parse(result)
        if _is_error(data):
            _assert_error_contract(data)
            return
        for key in ("running", "environment", "service", "base_url", "api_key_configured"):
            assert key in data, f"get_status success must include '{key}'"


class TestContractStopEngine:
    """Contract: stop_engine returns dict or error."""

    def test_stop_engine_valid_json(self) -> None:
        from baretrader.mcp.server import stop_engine

        result = stop_engine()
        data = _parse(result)
        assert isinstance(data, dict)

    def test_stop_engine_success_or_error_contract(self) -> None:
        from baretrader.mcp.server import stop_engine

        result = stop_engine()
        data = _parse(result)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            # Success: at least some response (e.g. status)
            assert isinstance(data, dict)


# =============================================================================
# Portfolio / market (often error without API key)
# =============================================================================


class TestContractPortfolioTools:
    """Contract: portfolio tools return documented shape or error."""

    def test_get_balance_contract(self) -> None:
        from baretrader.mcp.server import get_balance

        result = get_balance()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            assert "account" in data or "buying_power" in data or "equity" in data

    def test_get_positions_contract(self) -> None:
        from baretrader.mcp.server import get_positions

        result = get_positions()
        data = _parse(result)
        assert isinstance(data, dict | list)
        if isinstance(data, dict) and _is_error(data):
            _assert_error_contract(data)
        elif isinstance(data, list):
            for item in data:
                assert isinstance(item, dict)

    def test_get_portfolio_contract(self) -> None:
        from baretrader.mcp.server import get_portfolio

        result = get_portfolio()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            assert "total_equity" in data or "positions" in data

    def test_get_quote_contract(self) -> None:
        from baretrader.mcp.server import get_quote

        result = get_quote("AAPL")
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            for key in ("symbol", "bid", "ask", "last"):
                assert key in data, f"get_quote success must include '{key}'"


# =============================================================================
# Orders
# =============================================================================


class TestContractOrderTools:
    """Contract: order tools return list/dict or error."""

    def test_list_orders_contract(self) -> None:
        from baretrader.mcp.server import list_orders

        result = list_orders()
        data = _parse(result)
        assert isinstance(data, dict | list)
        if isinstance(data, dict) and _is_error(data):
            _assert_error_contract(data)


# =============================================================================
# Strategies
# =============================================================================


class TestContractStrategyTools:
    """Contract: strategy tools return documented shape or error."""

    def test_list_strategies_contract(self) -> None:
        from baretrader.mcp.server import list_strategies

        result = list_strategies()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            assert "strategies" in data, "list_strategies success must include 'strategies'"
            assert "count" in data, "list_strategies success must include 'count'"
            assert isinstance(data["strategies"], list)
            assert data["count"] == len(data["strategies"])

    def test_get_strategy_contract(self) -> None:
        from baretrader.mcp.server import get_strategy

        # Non-existent ID should still return valid contract (error)
        result = get_strategy("nonexistent-id-12345")
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            assert "id" in data and "symbol" in data


# =============================================================================
# Backtests
# =============================================================================


class TestContractBacktestTools:
    """Contract: backtest tools return list/dict or error."""

    def test_list_backtests_contract(self) -> None:
        from baretrader.mcp.server import list_backtests

        result = list_backtests()
        data = _parse(result)
        assert isinstance(data, list)

    def test_show_backtest_contract(self) -> None:
        from baretrader.mcp.server import show_backtest

        result = show_backtest("nonexistent-bt-id")
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)


# =============================================================================
# Analysis
# =============================================================================


class TestContractAnalysisTools:
    """Contract: analysis tools return documented shape or error."""

    def test_analyze_performance_contract(self) -> None:
        from baretrader.mcp.server import analyze_performance

        result = analyze_performance()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        elif "message" in data and "No trades" in str(data.get("message", "")):
            pass  # No trades found is valid
        else:
            # AnalysisResponse: summary, per_symbol, open_positions, unmatched_sell_qty
            assert "summary" in data or "total_trades" in data or "win_rate" in data

    def test_get_trade_history_contract(self) -> None:
        from baretrader.mcp.server import get_trade_history

        result = get_trade_history()
        data = _parse(result)
        assert isinstance(data, list)

    def test_get_today_pnl_contract(self) -> None:
        from baretrader.mcp.server import get_today_pnl

        result = get_today_pnl()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            assert "today_pnl" in data


# =============================================================================
# Indicators (no broker required for list/describe)
# =============================================================================


class TestContractIndicatorTools:
    """Contract: indicator tools return schema-valid shape or error."""

    def test_list_indicators_contract(self) -> None:
        from baretrader.mcp.server import list_indicators

        result = list_indicators()
        data = _parse(result)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            IndicatorInfo.model_validate(item)

    def test_describe_indicator_success_contract(self) -> None:
        from baretrader.mcp.server import describe_indicator

        result = describe_indicator("sma")
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            IndicatorInfo.model_validate(data)
            assert data["name"] == "sma"

    def test_describe_indicator_not_found_contract(self) -> None:
        from baretrader.mcp.server import describe_indicator

        result = describe_indicator("NONEXISTENT_XYZ")
        data = _parse(result)
        assert isinstance(data, dict)
        _assert_error_contract(data)


# =============================================================================
# Safety
# =============================================================================


class TestContractSafetyTools:
    """Contract: safety tool returns documented shape or error."""

    def test_get_safety_status_contract(self) -> None:
        from baretrader.mcp.server import get_safety_status

        result = get_safety_status()
        data = _parse(result)
        assert isinstance(data, dict)
        if _is_error(data):
            _assert_error_contract(data)
        else:
            # Response has "status" and optionally "limits"
            assert "status" in data
            status = data["status"]
            assert "kill_switch" in status
            assert "can_trade" in status


# =============================================================================
# Scheduling (list scheduled strategies)
# =============================================================================


class TestContractSchedulingTools:
    """Contract: scheduling tools return list/dict or error."""

    def test_list_scheduled_strategies_contract(self) -> None:
        from baretrader.mcp.server import list_scheduled_strategies

        result = list_scheduled_strategies()
        data = _parse(result)
        assert isinstance(data, dict | list)
        if isinstance(data, dict) and _is_error(data):
            _assert_error_contract(data)
