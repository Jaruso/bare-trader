"""Tests for the app service layer."""

from decimal import Decimal
from pathlib import Path

import pytest

from trader.app.indicators import describe_indicator, list_all_indicators
from trader.app.engine import get_engine_status, stop_engine
from trader.app.strategies import (
    get_strategy_detail,
    list_strategies,
    remove_strategy,
)
from trader.errors import (
    ConfigurationError,
    EngineError,
    NotFoundError,
)
from trader.schemas.indicators import IndicatorInfo
from trader.schemas.engine import EngineStatus
from trader.schemas.strategies import StrategyListResponse


class TestIndicatorServices:
    """Test indicator app services."""

    def test_list_all_indicators(self) -> None:
        """Should return a list of IndicatorInfo."""
        results = list_all_indicators()
        assert isinstance(results, list)
        assert len(results) > 0
        for item in results:
            assert isinstance(item, IndicatorInfo)
            assert item.name
            assert item.description

    def test_describe_indicator_known(self) -> None:
        """Should return info for a known indicator."""
        indicators = list_all_indicators()
        name = indicators[0].name
        result = describe_indicator(name)
        assert result.name == name

    def test_describe_indicator_not_found(self) -> None:
        """Should raise NotFoundError for unknown indicator."""
        with pytest.raises(NotFoundError) as exc_info:
            describe_indicator("NONEXISTENT_INDICATOR_XYZ")
        assert "NONEXISTENT_INDICATOR_XYZ" in exc_info.value.message


class TestEngineServices:
    """Test engine app services."""

    def test_get_engine_status_not_running(self) -> None:
        """When no lock file exists, engine is not running."""
        from trader.utils.config import load_config

        config = load_config()
        result = get_engine_status(config)
        assert isinstance(result, EngineStatus)
        assert result.running is False
        # environment comes from config.env.value.upper()
        assert result.environment == config.env.value.upper()

    def test_stop_engine_not_running(self) -> None:
        """Should raise EngineError if no engine is running."""
        with pytest.raises(EngineError):
            stop_engine(force=False)


class TestStrategyServices:
    """Test strategy app services."""

    def test_list_strategies_returns_response(self) -> None:
        """Should return a StrategyListResponse."""
        result = list_strategies()
        assert isinstance(result, StrategyListResponse)
        assert isinstance(result.strategies, list)
        assert result.count == len(result.strategies)

    def test_get_strategy_detail_not_found(self) -> None:
        """Should raise NotFoundError for unknown ID."""
        with pytest.raises(NotFoundError):
            get_strategy_detail("nonexistent-strategy-id-12345")

    def test_remove_strategy_not_found(self) -> None:
        """Should raise NotFoundError for unknown strategy."""
        with pytest.raises(NotFoundError):
            remove_strategy("nonexistent-strategy-id-12345")


class TestAppInit:
    """Test app/__init__.py get_broker helper."""

    def test_get_broker_missing_keys_raises(self) -> None:
        """Should raise ConfigurationError when API keys missing."""
        from trader.app import get_broker
        from trader.utils.config import (
            Config,
            Environment,
            Service,
            StrategyDefaults,
        )

        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="",
            alpaca_secret_key="",
            base_url="https://paper-api.alpaca.markets",
            data_dir=Path("data"),
            log_dir=Path("logs"),
            strategy_defaults=StrategyDefaults(),
        )
        with pytest.raises(ConfigurationError) as exc_info:
            get_broker(config)
        assert "not configured" in exc_info.value.message

    def test_get_broker_with_keys_returns_broker(self) -> None:
        """Should return a broker instance when keys are set."""
        from trader.app import get_broker
        from trader.api.broker import Broker
        from trader.utils.config import (
            Config,
            Environment,
            Service,
            StrategyDefaults,
        )

        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="test-key",
            alpaca_secret_key="test-secret",
            base_url="https://paper-api.alpaca.markets",
            data_dir=Path("data"),
            log_dir=Path("logs"),
            strategy_defaults=StrategyDefaults(),
        )
        broker = get_broker(config)
        assert isinstance(broker, Broker)


class TestCLIJsonFlag:
    """Test that --json flag is available on CLI commands."""

    def test_cli_status_json(self) -> None:
        """Status command should accept --json flag."""
        from click.testing import CliRunner
        from trader.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "status"])
        assert result.exit_code == 0

    def test_cli_strategy_list_json(self) -> None:
        """Strategy list should accept --json flag."""
        from click.testing import CliRunner
        from trader.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "strategy", "list"])
        assert result.exit_code == 0
