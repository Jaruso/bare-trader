"""Safety controls for trading."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from baretrader.api.broker import Broker
from baretrader.api.broker import OrderSide as BrokerOrderSide
from baretrader.api.broker import OrderStatus as BrokerOrderStatus
from baretrader.data.ledger import TradeLedger
from baretrader.models.order import OrderSide as LocalOrderSide
from baretrader.models.order import OrderStatus as LocalOrderStatus
from baretrader.oms.store import load_orders, save_order
from baretrader.utils.logging import get_logger


@dataclass
class SafetyLimits:
    """Safety limit configuration."""

    max_position_size: int = 100  # Max shares per position
    max_position_value: Decimal = Decimal("10000")  # Max $ per position
    max_daily_loss: Decimal = Decimal("500")  # Max daily loss before stopping
    max_daily_trades: int = 50  # Max trades per day
    max_order_value: Decimal = Decimal("5000")  # Max $ per single order


class SafetyCheck:
    """Safety control checks before executing trades."""

    def __init__(
        self,
        broker: Broker,
        ledger: TradeLedger,
        limits: SafetyLimits | None = None,
        orders_dir: Path | None = None,
    ) -> None:
        """Initialize safety checker.

        Args:
            broker: Broker instance.
            ledger: Trade ledger.
            limits: Safety limits (uses defaults if None).
        """
        self.broker = broker
        self.ledger = ledger
        self.limits = limits or SafetyLimits()
        self.orders_dir = orders_dir
        self.logger = get_logger("baretrader.safety")
        self._killed = False

    def kill(self) -> None:
        """Activate kill switch - stops all trading."""
        self._killed = True
        self.logger.warning("KILL SWITCH ACTIVATED - all trading stopped")

    def reset(self) -> None:
        """Reset kill switch."""
        self._killed = False
        self.logger.info("Kill switch reset")

    @property
    def is_killed(self) -> bool:
        """Check if kill switch is active."""
        return self._killed

    def check_can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed.

        Returns:
            Tuple of (can_trade, reason).
        """
        if self._killed:
            return False, "Kill switch is active"

        # Check daily loss limit
        daily_pnl = self.ledger.get_total_today_pnl()
        if daily_pnl < -self.limits.max_daily_loss:
            self.logger.warning(
                f"Daily loss limit reached: ${daily_pnl:.2f} (limit: -${self.limits.max_daily_loss})"
            )
            return False, f"Daily loss limit reached: ${daily_pnl:.2f}"

        # Check daily trade count
        trade_count = self.ledger.get_trade_count_today()
        if trade_count >= self.limits.max_daily_trades:
            self.logger.warning(
                f"Daily trade limit reached: {trade_count} (limit: {self.limits.max_daily_trades})"
            )
            return False, f"Daily trade limit reached: {trade_count} trades"

        return True, "OK"

    def check_order(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        is_buy: bool,
    ) -> tuple[bool, str]:
        """Check if a specific order is allowed.

        Args:
            symbol: Stock symbol.
            quantity: Number of shares.
            price: Order price.
            is_buy: True if buy order.

        Returns:
            Tuple of (allowed, reason).
        """
        # First check general trading permission
        can_trade, reason = self.check_can_trade()
        if not can_trade:
            return False, reason

        order_value = Decimal(str(quantity)) * price

        # Check order value limit
        if order_value > self.limits.max_order_value:
            return False, f"Order value ${order_value:.2f} exceeds limit ${self.limits.max_order_value}"

        # Get actual pending orders from broker (source of truth)
        # Also reconcile local orders.yaml with broker to keep it in sync
        try:
            broker_orders = self.broker.get_orders()
            # Filter to only pending orders for this symbol
            pending_broker_orders = [
                o for o in broker_orders
                if o.symbol == symbol
                and o.status in (
                    BrokerOrderStatus.NEW,
                    BrokerOrderStatus.PENDING,
                    BrokerOrderStatus.ACCEPTED,
                    BrokerOrderStatus.PARTIALLY_FILLED,
                )
            ]

            # Reconcile local orders.yaml with broker (update statuses)
            try:
                local_orders = load_orders(self.orders_dir)
                for local_order in local_orders:
                    if local_order.symbol != symbol:
                        continue
                    # Skip if already in final state
                    if local_order.status in (LocalOrderStatus.FILLED, LocalOrderStatus.CANCELED):
                        continue

                    # Find matching broker order
                    broker_order = None
                    for bo in broker_orders:
                        if (bo.id == local_order.id or
                            bo.id == local_order.external_id or
                            (local_order.external_id and bo.id == local_order.external_id)):
                            broker_order = bo
                            break

                    # Update local order if broker shows different status
                    if broker_order:
                        broker_status = broker_order.status
                        local_status = local_order.status
                        # Compare status values
                        broker_status_str = broker_status.value if hasattr(broker_status, 'value') else str(broker_status)
                        local_status_str = local_status.value if hasattr(local_status, 'value') else str(local_status)

                        if broker_status_str != local_status_str:
                            try:
                                # Save updated broker order to sync status
                                save_order(broker_order, self.orders_dir)
                                self.logger.debug(f"Reconciled order {local_order.id}: {local_status_str} -> {broker_status_str}")
                            except Exception as e:
                                self.logger.debug(f"Failed to reconcile order {local_order.id}: {e}")
            except Exception as e:
                self.logger.debug(f"Failed to reconcile local orders: {e}")
        except Exception as e:
            self.logger.debug(f"Failed to get broker orders, falling back to local: {e}")
            pending_broker_orders = []

        # Calculate pending quantities from broker orders (source of truth)
        pending_buy_qty = 0
        pending_buy_value = Decimal("0")
        pending_sell_qty = 0
        midpoint = None
        for o in pending_broker_orders:
            is_buy_order = o.side == BrokerOrderSide.BUY
            qty = int(o.qty)

            if is_buy_order:
                pending_buy_qty += qty
                # estimate value
                if o.limit_price is not None:
                    pending_buy_value += Decimal(str(o.limit_price)) * qty
                else:
                    # lazy fetch midpoint once
                    if midpoint is None:
                        try:
                            q = self.broker.get_quote(symbol)
                            midpoint = (q.bid + q.ask) / 2
                        except Exception:
                            midpoint = Decimal("0")
                    pending_buy_value += (midpoint or Decimal("0")) * qty
            else:
                pending_sell_qty += qty

        # When broker returned no pending orders (e.g. mock or API failure), use local orders dir so we still reserve buying power / position size
        if (pending_buy_qty == 0 and pending_sell_qty == 0) and self.orders_dir is not None:
            try:
                local_orders = load_orders(self.orders_dir)
                for local_order in local_orders:
                    if local_order.symbol != symbol:
                        continue
                    if local_order.status in (LocalOrderStatus.FILLED, LocalOrderStatus.CANCELED):
                        continue
                    qty = int(local_order.qty)
                    if local_order.side == LocalOrderSide.BUY:
                        pending_buy_qty += qty
                        if local_order.limit_price is not None:
                            pending_buy_value += local_order.limit_price * qty
                        else:
                            if midpoint is None:
                                try:
                                    q = self.broker.get_quote(symbol)
                                    midpoint = (q.bid + q.ask) / 2
                                except Exception:
                                    midpoint = Decimal("0")
                            pending_buy_value += (midpoint or Decimal("0")) * qty
                    else:
                        pending_sell_qty += qty
            except Exception as e:
                self.logger.debug(f"Failed to load local orders for pending reserve: {e}")

        # Check against current position quantity as well
        current_position = self.broker.get_position(symbol)
        current_qty = int(current_position.qty) if current_position else 0
        if current_qty + quantity + pending_buy_qty > self.limits.max_position_size and is_buy:
            return False, f"Quantity {quantity} plus pending {pending_buy_qty} and current {current_qty} exceeds position size limit {self.limits.max_position_size}"

        # For buys, check position limits
        if is_buy:
            # Check if this would exceed position value limit
            current_value = Decimal("0")
            if current_position:
                current_value = current_position.market_value

            new_value = current_value + order_value + pending_buy_value
            if new_value > self.limits.max_position_value:
                return (
                    False,
                    f"Position value ${new_value:.2f} would exceed limit ${self.limits.max_position_value}",
                )

            # Check account has sufficient buying power (subtract pending reserved value)
            account = self.broker.get_account()
            reserved = pending_buy_value
            available = account.buying_power - reserved
            if order_value > available:
                return False, f"Insufficient buying power: need ${order_value:.2f}, have ${available:.2f} after reserving pending orders"

        return True, "OK"

    def get_status(self) -> dict:
        """Get current safety status.

        Returns:
            Dict with safety metrics.
        """
        daily_pnl = self.ledger.get_total_today_pnl()
        trade_count = self.ledger.get_trade_count_today()

        return {
            "kill_switch": self._killed,
            "daily_pnl": daily_pnl,
            "daily_pnl_limit": -self.limits.max_daily_loss,
            "daily_pnl_remaining": self.limits.max_daily_loss + daily_pnl,
            "trade_count": trade_count,
            "trade_limit": self.limits.max_daily_trades,
            "trades_remaining": self.limits.max_daily_trades - trade_count,
            "can_trade": self.check_can_trade()[0],
        }
