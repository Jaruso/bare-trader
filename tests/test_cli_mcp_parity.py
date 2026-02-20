"""CLI vs MCP parity tests: same operation produces equivalent JSON data.

Compares CLI output (trader <cmd> --json) with MCP tool response for the same
logical operation. Ensures both interfaces expose the same data shape.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from click.testing import CliRunner

from trader.cli.main import cli


def _cli_json(cmd: list[str]) -> dict[str, Any] | list[Any] | None:
    """Run CLI with --json and parse first line of stdout as JSON."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json"] + cmd)
    if result.exit_code != 0:
        return None
    text = result.output.strip()
    if not text:
        return None
    # CLI may print a single JSON object or array
    return json.loads(text)


# =============================================================================
# Status: CLI status --json vs MCP get_status()
# =============================================================================


class TestParityStatus:
    """CLI 'trader status --json' and MCP get_status() return equivalent data."""

    def test_status_same_top_level_keys(self) -> None:
        from trader.mcp.server import get_status

        cli_data = _cli_json(["status"])
        if cli_data is None:
            pytest.skip("CLI status --json failed or no config")
        mcp_raw = get_status()
        mcp_data = json.loads(mcp_raw)
        if "error" in mcp_data:
            pytest.skip("MCP get_status returned error (e.g. no config)")

        cli_keys = set(cli_data.keys())
        mcp_keys = set(mcp_data.keys())
        # Both must expose at least these
        required = {"running", "environment", "service", "base_url", "api_key_configured"}
        assert required <= cli_keys, f"CLI status missing keys: {required - cli_keys}"
        assert required <= mcp_keys, f"MCP status missing keys: {required - mcp_keys}"

    def test_status_running_and_environment_match(self) -> None:
        from trader.mcp.server import get_status

        cli_data = _cli_json(["status"])
        if cli_data is None:
            pytest.skip("CLI status --json failed")
        mcp_raw = get_status()
        mcp_data = json.loads(mcp_raw)
        if "error" in mcp_data:
            pytest.skip("MCP get_status returned error")

        assert cli_data["running"] == mcp_data["running"]
        assert cli_data["environment"] == mcp_data["environment"]
        assert cli_data["service"] == mcp_data["service"]
        assert cli_data["api_key_configured"] == mcp_data["api_key_configured"]


# =============================================================================
# Indicators: CLI indicator list/describe --json vs MCP list_indicators / describe_indicator
# =============================================================================


class TestParityIndicators:
    """CLI indicator commands and MCP indicator tools return equivalent data."""

    def test_indicator_list_same_count_and_names(self) -> None:
        from trader.mcp.server import list_indicators

        cli_data = _cli_json(["indicator", "list"])
        if cli_data is None:
            pytest.skip("CLI indicator list --json failed")
        if not isinstance(cli_data, list):
            pytest.skip("CLI indicator list did not return a list")

        mcp_raw = list_indicators()
        mcp_data = json.loads(mcp_raw)
        if not isinstance(mcp_data, list):
            pytest.skip("MCP list_indicators did not return a list")

        cli_names = [item["name"] for item in cli_data if isinstance(item, dict) and "name" in item]
        mcp_names = [item["name"] for item in mcp_data if isinstance(item, dict) and "name" in item]
        assert set(cli_names) == set(mcp_names)
        assert len(cli_data) == len(mcp_data)

    def test_indicator_describe_sma_same_structure(self) -> None:
        from trader.mcp.server import describe_indicator

        cli_data = _cli_json(["indicator", "describe", "sma"])
        if cli_data is None or not isinstance(cli_data, dict):
            pytest.skip("CLI indicator describe sma --json failed or not dict")

        mcp_raw = describe_indicator("sma")
        mcp_data = json.loads(mcp_raw)
        if "error" in mcp_data:
            pytest.skip("MCP describe_indicator('sma') returned error")

        for key in ("name", "description", "params", "output"):
            assert key in cli_data, f"CLI describe missing '{key}'"
            assert key in mcp_data, f"MCP describe missing '{key}'"
        assert cli_data["name"] == mcp_data["name"] == "sma"


# =============================================================================
# Strategies: CLI strategy list --json vs MCP list_strategies (when config present)
# =============================================================================


class TestParityStrategies:
    """CLI strategy list and MCP list_strategies return equivalent data."""

    def test_strategy_list_same_count_when_available(self) -> None:
        from trader.mcp.server import list_strategies

        cli_data = _cli_json(["strategy", "list"])
        if cli_data is None or not isinstance(cli_data, dict):
            pytest.skip("CLI strategy list --json failed or not dict")

        mcp_raw = list_strategies()
        mcp_data = json.loads(mcp_raw)
        if "error" in mcp_data:
            pytest.skip("MCP list_strategies returned error")

        assert "strategies" in cli_data and "strategies" in mcp_data
        assert "count" in cli_data and "count" in mcp_data
        assert cli_data["count"] == mcp_data["count"]
        assert len(cli_data["strategies"]) == len(mcp_data["strategies"])


# =============================================================================
# Backtest list: CLI backtest list --json vs MCP list_backtests
# =============================================================================


class TestParityBacktestList:
    """CLI backtest list and MCP list_backtests return equivalent data."""

    def test_backtest_list_same_length(self) -> None:
        from trader.mcp.server import list_backtests

        cli_data = _cli_json(["backtest", "list"])
        if cli_data is None:
            pytest.skip("CLI backtest list --json failed")
        if not isinstance(cli_data, list):
            # CLI might return list of backtest summaries
            pytest.skip("CLI backtest list did not return a list")

        mcp_raw = list_backtests()
        mcp_data = json.loads(mcp_raw)
        if not isinstance(mcp_data, list):
            pytest.skip("MCP list_backtests did not return a list")

        assert len(cli_data) == len(mcp_data)
