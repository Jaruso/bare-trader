"""Backtest engine for running strategies on historical data."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd

from trader.api.broker import OrderStatus
from trader.backtest.broker import HistoricalBroker
from trader.backtest.results import BacktestResult, calculate_metrics
from trader.strategies.evaluator import ActionType, StrategyAction, StrategyEvaluator
from trader.strategies.models import Strategy, StrategyPhase
from trader.utils.config import StrategyDefaults
from trader.utils.logging import get_logger


class BacktestEngine:
    """Engine for running backtests on historical data.

    Unlike TradingEngine which polls in real-time, BacktestEngine
    processes historical bars sequentially and simulates order fills.
    """

    def __init__(
        self,
        broker: HistoricalBroker,
        strategy_config: dict,
        start_date: datetime,
        end_date: datetime,
        defaults: Optional[StrategyDefaults] = None,
    ) -> None:
        """Initialize backtest engine.

        Args:
            broker: Historical broker with loaded data.
            strategy_config: Strategy configuration dict.
            start_date: Backtest start date.
            end_date: Backtest end date.
            defaults: Strategy defaults (optional).
        """
        self.broker = broker
        self.start_date = start_date
        self.end_date = end_date
        self.logger = get_logger("autotrader.backtest")

        # Create strategy from config
        self.strategy = Strategy.from_dict(strategy_config)

        # Create evaluator
        if defaults is None:
            defaults = StrategyDefaults()
        self.evaluator = StrategyEvaluator(broker, defaults)

        # Track equity curve
        self.equity_curve: list[tuple[datetime, Decimal]] = []

    def run(self) -> BacktestResult:
        """Run the backtest and return results.

        Returns:
            BacktestResult with performance metrics.
        """
        self.logger.info(
            f"Starting backtest: {self.strategy.strategy_type.value} on "
            f"{self.strategy.symbol} from {self.start_date.date()} to {self.end_date.date()}"
        )

        # Get all timestamps from data
        symbol = self.strategy.symbol
        if symbol not in self.broker.data:
            raise ValueError(f"No data loaded for {symbol}")

        df = self.broker.data[symbol]
        timestamps = df.index

        # Filter to date range
        timestamps = timestamps[(timestamps >= self.start_date) & (timestamps <= self.end_date)]

        if len(timestamps) == 0:
            raise ValueError(f"No data in date range {self.start_date} to {self.end_date}")

        self.logger.info(f"Processing {len(timestamps)} bars...")

        # Process each bar
        for i, timestamp in enumerate(timestamps):
            # Advance broker to this bar
            self.broker.advance_to_bar(timestamp)

            # Evaluate strategy
            action = self.evaluator._evaluate_strategy(self.strategy)

            # Execute action if any
            if action:
                self._execute_action(action)

            # Record equity
            account = self.broker.get_account()
            self.equity_curve.append((timestamp, account.equity))

            # Log progress
            if (i + 1) % 50 == 0 or (i + 1) == len(timestamps):
                self.logger.info(
                    f"Processed {i + 1}/{len(timestamps)} bars | "
                    f"Phase: {self.strategy.phase.value} | "
                    f"Equity: ${account.equity:,.2f}"
                )

            # Stop if strategy completed or failed
            if self.strategy.is_terminal():
                self.logger.info(
                    f"Strategy reached terminal state: {self.strategy.phase.value}"
                )
                break

        # Get all filled orders
        filled_orders = self.broker.get_orders(status=OrderStatus.FILLED)

        # Calculate metrics
        result = calculate_metrics(
            filled_orders=filled_orders,
            equity_curve=self.equity_curve,
            initial_capital=self.broker._account.portfolio_value - self.broker._account.equity + self.broker._account.cash,
            strategy_type=self.strategy.strategy_type.value,
            symbol=self.strategy.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            strategy_config=self.strategy.to_dict(),
        )

        # Actually, use the initial cash as initial capital
        initial_capital = Decimal("100000.00")  # Default from broker
        if hasattr(self.broker, "_initial_cash"):
            initial_capital = self.broker._initial_cash
        elif self.equity_curve:
            # Try to infer from first equity point
            initial_capital = self.equity_curve[0][1]

        result.initial_capital = initial_capital

        self.logger.info(
            f"Backtest complete: Return {result.total_return_pct:.2f}% | "
            f"Win Rate {result.win_rate:.1f}% | "
            f"Trades {result.total_trades}"
        )

        return result

    def _execute_action(self, action: StrategyAction) -> bool:
        """Execute a strategy action in-memory.

        Unlike the live evaluator, this doesn't persist to YAML.

        Args:
            action: Action to execute.

        Returns:
            True if successful.
        """
        self.logger.debug(
            f"Executing {action.action_type.value}: {action.reason}"
        )

        try:
            if action.action_type == ActionType.PLACE_ENTRY_ORDER:
                return self._execute_place_entry(action)

            elif action.action_type == ActionType.PLACE_EXIT_ORDER:
                return self._execute_place_exit(action)

            elif action.action_type == ActionType.UPDATE_STATE:
                return self._execute_update_state(action)

            elif action.action_type == ActionType.COMPLETE:
                self.strategy.update_phase(StrategyPhase.COMPLETED)
                self.logger.info(f"Strategy completed: {action.reason}")
                return True

            elif action.action_type == ActionType.FAIL:
                self.strategy.update_phase(StrategyPhase.FAILED)
                self.logger.warning(f"Strategy failed: {action.reason}")
                return True

            elif action.action_type == ActionType.CANCEL_ORDER:
                if action.order_params and "order_id" in action.order_params:
                    return self.broker.cancel_order(action.order_params["order_id"])
                return False

        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return False

        return False

    def _execute_place_entry(self, action: StrategyAction) -> bool:
        """Place entry order."""
        if action.order_params is None:
            return False

        order = self.broker.place_order(**action.order_params)

        # Update strategy state
        self.strategy.entry_order_id = order.id
        self.strategy.update_phase(StrategyPhase.ENTRY_ACTIVE)

        self.logger.info(
            f"Entry order placed: {order.id} | {order.side.value} {order.qty} "
            f"{order.symbol} @ {order.order_type.value}"
        )

        # If already filled (market order), update immediately
        if order.status == OrderStatus.FILLED:
            self.strategy.entry_fill_price = order.filled_avg_price
            self.strategy.high_watermark = order.filled_avg_price
            self.strategy.update_phase(StrategyPhase.POSITION_OPEN)
            self.logger.info(f"Entry filled immediately at ${order.filled_avg_price}")

        return True

    def _execute_place_exit(self, action: StrategyAction) -> bool:
        """Place exit order."""
        if action.order_params is None:
            return False

        order = self.broker.place_order(**action.order_params)

        # Update strategy state
        self.strategy.exit_order_ids.append(order.id)
        self.strategy.update_phase(StrategyPhase.EXITING)

        self.logger.info(
            f"Exit order placed: {order.id} | {order.side.value} {order.qty} "
            f"{order.symbol} @ {order.order_type.value}"
        )

        return True

    def _execute_update_state(self, action: StrategyAction) -> bool:
        """Update strategy state."""
        if action.state_updates is None:
            return False

        for key, value in action.state_updates.items():
            if hasattr(self.strategy, key):
                setattr(self.strategy, key, value)

        self.strategy.updated_at = datetime.now()

        self.logger.debug(f"State updated: {action.state_updates}")

        return True
