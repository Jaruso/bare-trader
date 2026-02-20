"""Tests for optimization parameter normalization."""

from baretrader.app.optimization import _normalize_param_keys
from baretrader.errors import ValidationError
from baretrader.schemas.optimization import OptimizeRequest
from baretrader.utils.config import Config, Environment, Service, StrategyDefaults


def test_normalize_param_keys_take_profit() -> None:
    """Test that take_profit normalizes to take_profit_pct."""
    params = {"take_profit": [0.02, 0.05], "stop_loss": [0.01, 0.02]}
    normalized = _normalize_param_keys(params)
    assert "take_profit_pct" in normalized
    assert "stop_loss_pct" in normalized
    assert normalized["take_profit_pct"] == [0.02, 0.05]
    assert normalized["stop_loss_pct"] == [0.01, 0.02]
    assert "take_profit" not in normalized
    assert "stop_loss" not in normalized


def test_normalize_param_keys_canonical_preserved() -> None:
    """Test that canonical names (take_profit_pct) are preserved."""
    params = {"take_profit_pct": [0.02, 0.05], "stop_loss_pct": [0.01, 0.02]}
    normalized = _normalize_param_keys(params)
    assert normalized == params


def test_normalize_param_keys_mixed() -> None:
    """Test normalization with mixed short and canonical names."""
    params = {"take_profit": [0.02], "stop_loss_pct": [0.01]}
    normalized = _normalize_param_keys(params)
    assert "take_profit_pct" in normalized
    assert "stop_loss_pct" in normalized
    assert normalized["take_profit_pct"] == [0.02]
    assert normalized["stop_loss_pct"] == [0.01]


def test_optimization_with_short_param_names() -> None:
    """Test that run_optimization accepts short param names."""
    from pathlib import Path

    from baretrader.app.optimization import run_optimization

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

    # This should not raise ValidationError about missing take_profit_pct/stop_loss_pct
    # (it may fail for other reasons like missing data, but param validation should pass)
    request = OptimizeRequest(
        strategy_type="bracket",
        symbol="AAPL",
        start="2024-01-01",
        end="2024-01-10",
        params={"take_profit": [0.02], "stop_loss": [0.01]},  # Short names
        objective="total_return_pct",
        method="grid",
        data_source="csv",
        initial_capital=100000,
        save=False,
    )

    # Should not raise ValidationError for missing params (normalization happens first)
    # May raise other errors (e.g., data not found), but param validation should pass
    try:
        run_optimization(config, request)
    except ValidationError as e:
        # If it's a param validation error, that's a bug
        assert "take_profit_pct" not in e.message.lower()
        assert "stop_loss_pct" not in e.message.lower()
        assert "missing required parameters" not in e.message.lower()
    except Exception:
        # Other errors (data not found, etc.) are acceptable
        pass
