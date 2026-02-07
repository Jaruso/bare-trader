"""Strategy evaluation engine.

This module evaluates trading strategies and determines what actions to take
based on current market conditions and strategy state.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from trader.api.broker import Broker, OrderSide, OrderType
from trader.strategies.models import Strategy, StrategyPhase, StrategyType, EntryType
from trader.strategies.loader import save_strategy, get_strategy
from trader.utils.config import StrategyDefaults
from trader.utils.logging import get_logger
from trader.oms.store import save_order


class ActionType(Enum):
    """Types of actions the evaluator can recommend."""

    PLACE_ENTRY_ORDER = "place_entry_order"
    PLACE_EXIT_ORDER = "place_exit_order"
    UPDATE_STATE = "update_state"
    CANCEL_ORDER = "cancel_order"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass
class StrategyAction:
    """An action to take for a strategy.

    The evaluator returns these to indicate what should happen.
    The engine then executes them.
    """

    strategy_id: str
    action_type: ActionType
    order_params: Optional[dict] = None  # For placing orders
    state_updates: Optional[dict] = None  # For state updates
    reason: Optional[str] = None


class StrategyEvaluator:
    """Evaluates and manages trading strategies.

    The evaluator checks each active strategy and determines what actions
    to take based on the strategy's current phase and market conditions.
    """

    def __init__(self, broker: Broker, defaults: StrategyDefaults) -> None:
        """Initialize the evaluator.

        Args:
            broker: Broker instance for market data and order execution.
            defaults: Default strategy parameters.
        """
        self.broker = broker
        self.defaults = defaults
        self.logger = get_logger("autotrader.strategies")

    def evaluate(self, strategies: list[Strategy]) -> list[StrategyAction]:
        """Evaluate all strategies and return required actions.

        Args:
            strategies: List of strategies to evaluate.

        Returns:
            List of actions to take.
        """
        actions = []

        for strategy in strategies:
            if not strategy.enabled:
                continue

            if strategy.is_terminal():
                continue

            try:
                action = self._evaluate_strategy(strategy)
                if action:
                    actions.append(action)
            except Exception as e:
                self.logger.error(f"Error evaluating strategy {strategy.id}: {e}")

        return actions

    def _evaluate_strategy(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate a single strategy based on its phase.

        Args:
            strategy: The strategy to evaluate.

        Returns:
            An action to take, or None if no action needed.
        """
        phase_handlers = {
            StrategyPhase.PENDING: self._evaluate_pending,
            StrategyPhase.ENTRY_ACTIVE: self._evaluate_entry_active,
            StrategyPhase.POSITION_OPEN: self._evaluate_position_open,
            StrategyPhase.EXITING: self._evaluate_exiting,
            StrategyPhase.PAUSED: lambda s: None,  # No action when paused
        }

        handler = phase_handlers.get(strategy.phase)
        if handler:
            return handler(strategy)
        return None

    def _evaluate_pending(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate a strategy waiting for entry.

        For market entries, immediately place the order.
        For limit entries, check if price condition is met.
        For conditional entries, check the condition.
        """
        if strategy.entry_type == EntryType.MARKET:
            # Place market entry immediately
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.PLACE_ENTRY_ORDER,
                order_params={
                    "symbol": strategy.symbol,
                    "qty": Decimal(str(strategy.quantity)),
                    "side": OrderSide.BUY,
                    "order_type": OrderType.MARKET,
                },
                reason="Market entry triggered",
            )

        elif strategy.entry_type == EntryType.LIMIT:
            if strategy.entry_price is None:
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.FAIL,
                    reason="Limit entry requires entry_price",
                )

            # Place limit order
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.PLACE_ENTRY_ORDER,
                order_params={
                    "symbol": strategy.symbol,
                    "qty": Decimal(str(strategy.quantity)),
                    "side": OrderSide.BUY,
                    "order_type": OrderType.LIMIT,
                    "limit_price": strategy.entry_price,
                },
                reason=f"Limit entry at ${strategy.entry_price}",
            )

        elif strategy.entry_type == EntryType.CONDITION:
            # Parse condition like "below:170.00" or "above:200.00"
            if not strategy.entry_condition:
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.FAIL,
                    reason="Conditional entry requires entry_condition",
                )

            try:
                parts = strategy.entry_condition.split(":")
                condition_type = parts[0].lower()
                target_price = Decimal(parts[1])
            except (IndexError, ValueError):
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.FAIL,
                    reason=f"Invalid entry_condition format: {strategy.entry_condition}",
                )

            # Get current price
            quote = self.broker.get_quote(strategy.symbol)
            current_price = (quote.bid + quote.ask) / 2

            # Check condition
            triggered = False
            if condition_type == "below" and current_price <= target_price:
                triggered = True
            elif condition_type == "above" and current_price >= target_price:
                triggered = True

            if triggered:
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.PLACE_ENTRY_ORDER,
                    order_params={
                        "symbol": strategy.symbol,
                        "qty": Decimal(str(strategy.quantity)),
                        "side": OrderSide.BUY,
                        "order_type": OrderType.MARKET,
                    },
                    reason=f"Condition met: price {condition_type} ${target_price}",
                )

        return None

    def _evaluate_entry_active(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Check if entry order has filled."""
        if not strategy.entry_order_id:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason="Entry active but no entry_order_id",
            )

        order = self.broker.get_order(strategy.entry_order_id)
        if order is None:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason=f"Entry order {strategy.entry_order_id} not found",
            )

        from trader.api.broker import OrderStatus

        if order.status == OrderStatus.FILLED:
            # Entry filled! Update state and move to position_open
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.UPDATE_STATE,
                state_updates={
                    "phase": StrategyPhase.POSITION_OPEN,
                    "entry_fill_price": order.filled_avg_price,
                    "high_watermark": order.filled_avg_price,  # Initialize watermark
                },
                reason=f"Entry filled at ${order.filled_avg_price}",
            )

        elif order.status in (OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED):
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason=f"Entry order {order.status.value}",
            )

        # Still pending, no action needed
        return None

    def _evaluate_position_open(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate an open position based on strategy type."""
        if strategy.strategy_type == StrategyType.TRAILING_STOP:
            return self._evaluate_trailing_stop(strategy)
        elif strategy.strategy_type == StrategyType.BRACKET:
            return self._evaluate_bracket(strategy)
        elif strategy.strategy_type == StrategyType.SCALE_OUT:
            return self._evaluate_scale_out(strategy)
        elif strategy.strategy_type == StrategyType.GRID:
            return self._evaluate_grid(strategy)

        return None

    def _evaluate_trailing_stop(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate trailing stop strategy.

        Updates high watermark as price rises. When no exit order exists,
        places a trailing stop order via the broker.
        """
        if strategy.trailing_stop_pct is None:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason="Trailing stop strategy missing trailing_stop_pct",
            )

        # Get current price
        quote = self.broker.get_quote(strategy.symbol)
        current_price = (quote.bid + quote.ask) / 2

        # Update high watermark if price has risen
        if strategy.high_watermark is None or current_price > strategy.high_watermark:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.UPDATE_STATE,
                state_updates={"high_watermark": current_price},
                reason=f"High watermark updated to ${current_price:.2f}",
            )

        # If no exit order placed yet, place trailing stop with broker
        if not strategy.exit_order_ids:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.PLACE_EXIT_ORDER,
                order_params={
                    "symbol": strategy.symbol,
                    "qty": Decimal(str(strategy.quantity)),
                    "side": OrderSide.SELL,
                    "order_type": OrderType.TRAILING_STOP,
                    "trail_percent": strategy.trailing_stop_pct,
                },
                reason=f"Placing {strategy.trailing_stop_pct}% trailing stop",
            )

        return None

    def _evaluate_bracket(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate bracket (OCO) strategy.

        Places both take-profit and stop-loss orders, cancels the other
        when one fills.
        """
        if strategy.take_profit_pct is None or strategy.stop_loss_pct is None:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason="Bracket strategy requires take_profit_pct and stop_loss_pct",
            )

        if strategy.entry_fill_price is None:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason="Bracket strategy requires entry_fill_price",
            )

        # Calculate target prices
        take_profit_price = strategy.entry_fill_price * (1 + strategy.take_profit_pct / 100)
        stop_loss_price = strategy.entry_fill_price * (1 - strategy.stop_loss_pct / 100)

        # If no exit orders yet, place take-profit first
        # (In a real implementation, you'd place both and track them)
        if not strategy.exit_order_ids:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.PLACE_EXIT_ORDER,
                order_params={
                    "symbol": strategy.symbol,
                    "qty": Decimal(str(strategy.quantity)),
                    "side": OrderSide.SELL,
                    "order_type": OrderType.LIMIT,
                    "limit_price": take_profit_price,
                },
                reason=f"Placing take-profit at ${take_profit_price:.2f}",
            )

        # TODO: Full bracket implementation would track both orders
        # and cancel the remaining one when first fills

        return None

    def _evaluate_scale_out(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate scale-out strategy.

        Sells portions at progressive profit targets.
        """
        # TODO: Implement scale-out evaluation
        # Would track tranches and place sell orders at each target
        return None

    def _evaluate_grid(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Evaluate grid strategy.

        Places buy orders at intervals going down, sell orders going up.
        """
        # TODO: Implement grid evaluation
        return None

    def _evaluate_exiting(self, strategy: Strategy) -> Optional[StrategyAction]:
        """Check if exit orders have filled."""
        if not strategy.exit_order_ids:
            return StrategyAction(
                strategy_id=strategy.id,
                action_type=ActionType.FAIL,
                reason="Exiting phase but no exit_order_ids",
            )

        from trader.api.broker import OrderStatus

        # Check all exit orders
        for order_id in strategy.exit_order_ids:
            order = self.broker.get_order(order_id)
            if order is None:
                continue

            if order.status == OrderStatus.FILLED:
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.COMPLETE,
                    reason=f"Exit order filled at ${order.filled_avg_price}",
                )

            elif order.status in (OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED):
                return StrategyAction(
                    strategy_id=strategy.id,
                    action_type=ActionType.FAIL,
                    reason=f"Exit order {order.status.value}",
                )

        return None

    def execute_action(self, action: StrategyAction, dry_run: bool = False) -> bool:
        """Execute a strategy action.

        Args:
            action: The action to execute.
            dry_run: If True, log but don't actually execute.

        Returns:
            True if action was successful.
        """
        strategy = get_strategy(action.strategy_id)
        if strategy is None:
            self.logger.error(f"Strategy {action.strategy_id} not found")
            return False

        prefix = "[DRY RUN] " if dry_run else ""
        self.logger.info(f"{prefix}Executing {action.action_type.value} for {strategy.symbol}: {action.reason}")

        if dry_run:
            return True

        try:
            if action.action_type == ActionType.PLACE_ENTRY_ORDER:
                return self._execute_place_entry(strategy, action)

            elif action.action_type == ActionType.PLACE_EXIT_ORDER:
                return self._execute_place_exit(strategy, action)

            elif action.action_type == ActionType.UPDATE_STATE:
                return self._execute_update_state(strategy, action)

            elif action.action_type == ActionType.COMPLETE:
                strategy.update_phase(StrategyPhase.COMPLETED)
                save_strategy(strategy)
                self.logger.info(f"Strategy {strategy.id} completed: {action.reason}")
                return True

            elif action.action_type == ActionType.FAIL:
                strategy.update_phase(StrategyPhase.FAILED)
                strategy.notes = action.reason
                save_strategy(strategy)
                self.logger.error(f"Strategy {strategy.id} failed: {action.reason}")
                return True

            elif action.action_type == ActionType.CANCEL_ORDER:
                # TODO: Implement order cancellation
                return True

        except Exception as e:
            self.logger.error(f"Error executing action for strategy {strategy.id}: {e}")
            return False

        return False

    def _execute_place_entry(self, strategy: Strategy, action: StrategyAction) -> bool:
        """Place an entry order and update strategy state."""
        if action.order_params is None:
            return False

        order = self.broker.place_order(**action.order_params)

        # Persist order locally
        try:
            save_order(order)
        except Exception as e:
            self.logger.warning(f"Failed to persist entry order: {e}")

        # Update strategy state
        strategy.entry_order_id = order.id
        strategy.update_phase(StrategyPhase.ENTRY_ACTIVE)
        save_strategy(strategy)

        self.logger.info(f"Entry order {order.id} placed for strategy {strategy.id}")
        return True

    def _execute_place_exit(self, strategy: Strategy, action: StrategyAction) -> bool:
        """Place an exit order and update strategy state."""
        if action.order_params is None:
            return False

        order = self.broker.place_order(**action.order_params)

        # Persist order locally
        try:
            save_order(order)
        except Exception as e:
            self.logger.warning(f"Failed to persist exit order: {e}")

        # Update strategy state
        strategy.exit_order_ids.append(order.id)
        strategy.update_phase(StrategyPhase.EXITING)
        save_strategy(strategy)

        self.logger.info(f"Exit order {order.id} placed for strategy {strategy.id}")
        return True

    def _execute_update_state(self, strategy: Strategy, action: StrategyAction) -> bool:
        """Update strategy state without placing orders."""
        if action.state_updates is None:
            return False

        for key, value in action.state_updates.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)

        strategy.updated_at = datetime.now()
        save_strategy(strategy)
        return True

    def run_once(self, strategies: list[Strategy], dry_run: bool = False) -> list[str]:
        """Evaluate all strategies and execute actions.

        Args:
            strategies: List of strategies to evaluate.
            dry_run: If True, don't actually execute.

        Returns:
            List of strategy IDs that had actions executed.
        """
        actions = self.evaluate(strategies)

        if not actions:
            self.logger.debug("No strategy actions needed")
            return []

        executed_ids = []
        for action in actions:
            if self.execute_action(action, dry_run=dry_run):
                executed_ids.append(action.strategy_id)

        return executed_ids
