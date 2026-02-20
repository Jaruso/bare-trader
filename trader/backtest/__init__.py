"""Backtesting module for BareTrader.

This module provides backtesting capabilities to test trading strategies
against historical data before risking real capital.
"""

from baretrader.backtest.broker import HistoricalBroker
from baretrader.backtest.data import load_csv_data, load_data_for_backtest
from baretrader.backtest.engine import BacktestEngine
from baretrader.backtest.results import BacktestResult
from baretrader.backtest.store import (
    delete_backtest,
    list_backtests,
    load_backtest,
    save_backtest,
)

__all__ = [
    "HistoricalBroker",
    "load_csv_data",
    "load_data_for_backtest",
    "BacktestEngine",
    "BacktestResult",
    "save_backtest",
    "load_backtest",
    "list_backtests",
    "delete_backtest",
]
