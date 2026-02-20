"""Interactive charting for backtest results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from bokeh.embed import json_item
from bokeh.io import output_file, save, show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure

from baretrader.backtest.results import BacktestResult


@dataclass
class IndicatorOverlay:
    """Indicator overlay configuration."""

    name: str
    series: pd.Series
    color: str = "#fbbf24"
    line_width: int = 2


class ChartBuilder:
    """Builds interactive charts from backtest results."""

    def __init__(
        self,
        result: BacktestResult,
        price_data: pd.DataFrame | None = None,
        theme: str = "dark",
    ) -> None:
        self.result = result
        self.price_data = price_data
        self.theme = theme
        self._indicators: list[IndicatorOverlay] = []
        self._layout = None

    def add_indicator(
        self, name: str, series: pd.Series, color: str = "#fbbf24", line_width: int = 2
    ) -> None:
        """Add an indicator overlay to the price chart."""
        self._indicators.append(
            IndicatorOverlay(name=name, series=series, color=color, line_width=line_width)
        )

    def build(self):
        """Create interactive chart layout."""
        if self._indicators and self.price_data is None:
            raise ValueError("Indicators require price data to be loaded")

        price_fig = self._build_price_chart() if self.price_data is not None else None
        equity_fig = self._build_equity_chart()

        if price_fig:
            self._layout = column(price_fig, equity_fig, sizing_mode="stretch_width")
        else:
            self._layout = column(equity_fig, sizing_mode="stretch_width")

        return self._layout

    def save_html(self, filepath: str) -> None:
        """Save chart to a standalone HTML file."""
        if self._layout is None:
            self.build()
        output_file(filepath, title=f"Backtest {self.result.id}")
        save(self._layout)

    def to_json(self) -> dict:
        """Export chart as a JSON item (for MCP integration)."""
        if self._layout is None:
            self.build()
        return json_item(self._layout)

    def show(self) -> None:
        """Open the chart in a browser."""
        if self._layout is None:
            self.build()
        show(self._layout)

    def _build_price_chart(self) -> Any:
        df = self.price_data
        if df is None:
            raise ValueError("Price data is required to build price chart")

        df = df.copy()
        df = df.sort_index()
        df["timestamp"] = pd.to_datetime(df.index)

        bar_width_ms = _calculate_bar_width_ms(df["timestamp"])

        inc = df["close"] >= df["open"]
        dec = df["close"] < df["open"]

        source = ColumnDataSource(df)
        p = figure(
            x_axis_type="datetime",
            height=420,
            title=f"{self.result.symbol} Price",
            sizing_mode="stretch_width",
            toolbar_location="above",
        )
        self._apply_theme(p)

        p.segment("timestamp", "high", "timestamp", "low", color="#94a3b8", source=source)
        p.vbar(
            "timestamp",
            bar_width_ms,
            "open",
            "close",
            fill_color="#22c55e",
            line_color="#22c55e",
            source=ColumnDataSource(df[inc]),
        )
        p.vbar(
            "timestamp",
            bar_width_ms,
            "open",
            "close",
            fill_color="#ef4444",
            line_color="#ef4444",
            source=ColumnDataSource(df[dec]),
        )

        self._add_trade_markers(p, df)
        self._add_indicators(p, df)

        p.add_tools(
            HoverTool(
                tooltips=[
                    ("Date", "@timestamp{%F}"),
                    ("Open", "@open{0.00}"),
                    ("High", "@high{0.00}"),
                    ("Low", "@low{0.00}"),
                    ("Close", "@close{0.00}"),
                    ("Volume", "@volume{0,0}"),
                ],
                formatters={"@timestamp": "datetime"},
                mode="vline",
            )
        )

        return p

    def _build_equity_chart(self) -> Any:
        equity_data = [
            (ts, float(equity)) for ts, equity in self.result.equity_curve
        ]
        equity_df = pd.DataFrame(equity_data, columns=["timestamp", "equity"])

        p = figure(
            x_axis_type="datetime",
            height=240,
            title="Equity Curve",
            sizing_mode="stretch_width",
            toolbar_location="above",
        )
        self._apply_theme(p)

        if not equity_df.empty:
            p.line(
                equity_df["timestamp"],
                equity_df["equity"],
                line_width=2,
                color="#60a5fa",
            )
            p.add_tools(
                HoverTool(
                    tooltips=[
                        ("Date", "@x{%F}"),
                        ("Equity", "@y{$0,0.00}"),
                    ],
                    formatters={"@x": "datetime"},
                    mode="vline",
                )
            )

        return p

    def _add_trade_markers(self, fig: Any, df: pd.DataFrame) -> None:
        trades = self._normalize_trades()
        if not trades:
            return

        buys = [t for t in trades if t["side"] == "buy"]
        sells = [t for t in trades if t["side"] == "sell"]

        if buys:
            buy_source = ColumnDataSource(_trades_to_source(buys))
            fig.scatter(
                "timestamp",
                "price",
                marker="triangle",
                size=10,
                color="#22c55e",
                legend_label="Buy",
                source=buy_source,
            )
        if sells:
            sell_source = ColumnDataSource(_trades_to_source(sells))
            fig.scatter(
                "timestamp",
                "price",
                marker="inverted_triangle",
                size=10,
                color="#ef4444",
                legend_label="Sell",
                source=sell_source,
            )

    def _add_indicators(self, fig: Any, df: pd.DataFrame) -> None:
        if not self._indicators:
            return

        for indicator in self._indicators:
            series = indicator.series.reindex(df.index)
            fig.line(
                df["timestamp"],
                series,
                line_width=indicator.line_width,
                color=indicator.color,
                legend_label=indicator.name,
            )

    def _normalize_trades(self) -> list[dict]:
        trades = []
        for trade in self.result.trades:
            timestamp = _parse_trade_timestamp(trade.get("timestamp"))
            if timestamp is None:
                continue
            price = trade.get("price")
            if price is None:
                continue
            trades.append(
                {
                    "timestamp": timestamp,
                    "price": float(Decimal(str(price))),
                    "side": trade.get("side", "").lower(),
                }
            )
        return trades

    def _apply_theme(self, fig: Any) -> None:
        if self.theme == "light":
            fig.background_fill_color = "#ffffff"
            fig.border_fill_color = "#ffffff"
            fig.grid.grid_line_color = "#e2e8f0"
            fig.outline_line_color = "#e2e8f0"
        else:
            fig.background_fill_color = "#0f172a"
            fig.border_fill_color = "#0f172a"
            fig.grid.grid_line_color = "#334155"
            fig.outline_line_color = "#334155"


def _parse_trade_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return pd.to_datetime(value).to_pydatetime()
        except Exception:
            return None


def _calculate_bar_width_ms(timestamps: pd.Series) -> int:
    if len(timestamps) < 2:
        return 12 * 60 * 60 * 1000

    diffs = timestamps.sort_values().diff().dropna()
    median_delta = diffs.median()
    if pd.isna(median_delta):
        return 12 * 60 * 60 * 1000
    ms = int(median_delta.total_seconds() * 1000)
    return max(int(ms * 0.7), 1)


def _trades_to_source(trades: list[dict]) -> dict:
    return {
        "timestamp": [t["timestamp"] for t in trades],
        "price": [t["price"] for t in trades],
        "side": [t["side"] for t in trades],
    }
