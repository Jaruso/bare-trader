"""Tests for backtest visualization."""

from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd

from trader.backtest.results import BacktestResult
from trader.visualization.chart import ChartBuilder


def _sample_result() -> BacktestResult:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 5)
    equity_curve = [
        (start + timedelta(days=idx), Decimal("100000") + Decimal(idx * 500))
        for idx in range(5)
    ]
    trades = [
        {
            "id": "t1",
            "timestamp": (start + timedelta(days=1)).isoformat(),
            "symbol": "AAPL",
            "side": "buy",
            "qty": "10",
            "price": "175.25",
            "total": "1752.50",
        },
        {
            "id": "t2",
            "timestamp": (start + timedelta(days=3)).isoformat(),
            "symbol": "AAPL",
            "side": "sell",
            "qty": "10",
            "price": "180.75",
            "total": "1807.50",
        },
    ]

    return BacktestResult(
        id="abcd1234",
        strategy_type="trailing_stop",
        symbol="AAPL",
        start_date=start,
        end_date=end,
        created_at=datetime(2024, 1, 6),
        strategy_config={"symbol": "AAPL", "strategy_type": "trailing_stop"},
        initial_capital=Decimal("100000"),
        total_return=Decimal("5000"),
        total_return_pct=Decimal("5"),
        win_rate=Decimal("50"),
        profit_factor=Decimal("1.2"),
        max_drawdown=Decimal("1000"),
        max_drawdown_pct=Decimal("1"),
        sharpe_ratio=None,
        total_trades=2,
        winning_trades=1,
        losing_trades=1,
        avg_win=Decimal("500"),
        avg_loss=Decimal("-250"),
        largest_win=Decimal("500"),
        largest_loss=Decimal("-250"),
        equity_curve=equity_curve,
        trades=trades,
    )


def _sample_price_data() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "open": [175, 176, 177, 178, 179],
            "high": [176, 177, 178, 179, 180],
            "low": [174, 175, 176, 177, 178],
            "close": [175.5, 176.5, 177.5, 178.5, 179.5],
            "volume": [1000000, 1100000, 900000, 950000, 1050000],
        },
        index=index,
    )


def test_build_chart_with_price_data() -> None:
    result = _sample_result()
    builder = ChartBuilder(result=result, price_data=_sample_price_data())
    layout = builder.build()
    assert layout is not None


def test_build_chart_with_indicator() -> None:
    result = _sample_result()
    price_data = _sample_price_data()
    builder = ChartBuilder(result=result, price_data=price_data)
    builder.add_indicator("SMA", price_data["close"].rolling(2).mean())
    layout = builder.build()
    assert layout is not None


def test_build_equity_only_chart() -> None:
    result = _sample_result()
    builder = ChartBuilder(result=result, price_data=None)
    layout = builder.build()
    assert layout is not None


def test_save_chart_html(tmp_path) -> None:
    result = _sample_result()
    builder = ChartBuilder(result=result, price_data=_sample_price_data())
    output_path = tmp_path / "chart.html"
    builder.save_html(str(output_path))
    assert output_path.exists()
