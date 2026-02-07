"""Backtesting module for AutoTrader.

This module provides backtesting capabilities to test trading strategies
against historical data before risking real capital.
"""

from trader.backtest.broker import HistoricalBroker
from trader.backtest.data import load_csv_data, load_data_for_backtest
from trader.backtest.engine import BacktestEngine
from trader.backtest.results import BacktestResult
from trader.backtest.store import (
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
