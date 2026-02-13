"""Historical broker for backtesting.

This broker simulates order fills based on historical OHLCV data.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from trader.api.broker import (
    Account,
    Broker,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Quote,
)
from trader.utils.logging import get_logger


class HistoricalBroker(Broker):
    """Broker that simulates trading on historical data.

    This broker replays historical price data and simulates order fills
    based on OHLCV bars.

    Fill Simulation Rules:
    - Market orders: Fill at current bar's close price
    - Limit orders: Fill at limit price if within bar [low, high] range
    - Stop orders: Fill at stop price if triggered by bar range
    - Trailing stop: Track high watermark, trigger on pullback threshold
    """

    def __init__(
        self,
        historical_data: dict[str, pd.DataFrame],
        initial_cash: Decimal = Decimal("100000.00"),
    ) -> None:
        """Initialize historical broker.

        Args:
            historical_data: Dict mapping symbol to OHLCV DataFrame.
                DataFrame must have index=timestamp and columns: open, high, low, close, volume.
            initial_cash: Starting capital.
        """
        self.data = historical_data
        self.logger = get_logger("autotrader.backtest.broker")
        self.initial_cash = initial_cash  # Store for metrics calculation

        # Current state
        self.current_timestamp: datetime | None = None
        self.current_bar_index: dict[str, int] = {symbol: 0 for symbol in historical_data}

        # Account state
        self._account = Account(
            cash=initial_cash,
            buying_power=initial_cash,  # No margin for backtesting
            equity=initial_cash,
            portfolio_value=initial_cash,
            currency="USD",
        )

        # Positions and orders
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, Order] = {}
        self._next_order_id = 1

        # Trailing stop tracking
        self._trailing_stop_highs: dict[str, Decimal] = {}  # order_id -> high watermark

    def advance_to_bar(self, timestamp: datetime) -> None:
        """Advance broker to a specific timestamp.

        This updates the current bar for all symbols and processes
        any pending orders that should fill.

        Args:
            timestamp: Timestamp to advance to.
        """
        self.current_timestamp = timestamp

        # Update bar indices for all symbols
        for symbol, df in self.data.items():
            # Find the index for this timestamp
            if timestamp in df.index:
                self.current_bar_index[symbol] = df.index.get_loc(timestamp)

        # Process pending orders (check for fills)
        self._process_pending_orders()

        # Update account equity
        self._update_account()

    def get_account(self) -> Account:
        """Get account information."""
        return self._account

    def get_positions(self) -> list[Position]:
        """Get all open positions."""
        return list(self._positions.values())

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        return self._positions.get(symbol)

    def get_quote(self, symbol: str) -> Quote:
        """Get current quote for a symbol.

        Uses the current bar's close price for bid/ask/last.

        Args:
            symbol: Stock symbol.

        Returns:
            Current quote.
        """
        if symbol not in self.data:
            raise ValueError(f"No data for symbol: {symbol}")

        df = self.data[symbol]
        idx = self.current_bar_index[symbol]

        if idx >= len(df):
            raise ValueError(f"No more data for {symbol} at index {idx}")

        bar = df.iloc[idx]

        # Use close as bid/ask/last (simplified)
        close = Decimal(str(bar["close"]))

        return Quote(
            symbol=symbol,
            bid=close,
            ask=close,
            last=close,
            volume=int(bar["volume"]),
        )

    def place_order(
        self,
        symbol: str,
        qty: Decimal,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        trail_percent: Decimal | None = None,
    ) -> Order:
        """Place a trade order.

        Market orders fill immediately at current bar close.
        Limit/stop orders remain pending until conditions met.

        Args:
            symbol: Stock symbol.
            qty: Number of shares.
            side: Buy or sell.
            order_type: Market, limit, stop, or trailing_stop.
            limit_price: Limit price for limit orders.
            stop_price: Stop price for stop orders.
            trail_percent: Trail percentage for trailing stop orders.

        Returns:
            Created order.
        """
        order_id = f"backtest-{self._next_order_id}"
        self._next_order_id += 1

        # Market orders fill immediately
        if order_type == OrderType.MARKET:
            quote = self.get_quote(symbol)
            fill_price = quote.last

            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                qty=qty,
                status=OrderStatus.FILLED,
                filled_qty=qty,
                filled_avg_price=fill_price,
                created_at=str(self.current_timestamp),
            )

            # Update position
            self._update_position(order)

            self.logger.info(
                f"Market order filled: {side.value} {qty} {symbol} @ {fill_price}"
            )

        else:
            # Limit/stop orders start as NEW
            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                qty=qty,
                status=OrderStatus.NEW,
                filled_qty=Decimal("0"),
                limit_price=limit_price,
                stop_price=stop_price,
                trail_percent=trail_percent,
                created_at=str(self.current_timestamp),
            )

            # Initialize trailing stop high watermark
            if order_type == OrderType.TRAILING_STOP:
                quote = self.get_quote(symbol)
                self._trailing_stop_highs[order_id] = quote.last

            self.logger.info(
                f"Order placed: {side.value} {qty} {symbol} "
                f"type={order_type.value} limit={limit_price} stop={stop_price}"
            )

        self._orders[order_id] = order
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if order_id in self._orders:
            order = self._orders[order_id]
            if order.status in (OrderStatus.NEW, OrderStatus.PENDING):
                order.status = OrderStatus.CANCELED
                self.logger.info(f"Order canceled: {order_id}")
                return True
        return False

    def get_order(self, order_id: str) -> Order | None:
        """Get order by ID."""
        return self._orders.get(order_id)

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        """Get orders, optionally filtered by status."""
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders

    def is_market_open(self) -> bool:
        """Check if market is currently open.

        For backtesting, market is always "open" during data range.
        """
        return True

    def _process_pending_orders(self) -> None:
        """Process pending orders and check for fills.

        Only one order per symbol fills per bar to simulate OCO behavior.
        If both a limit and stop could fill on the same bar, only the first
        (by order ID) will fill. The strategy evaluator then cancels the other.
        """
        filled_symbols: set[str] = set()

        for order in list(self._orders.values()):
            if order.status not in (OrderStatus.NEW, OrderStatus.PENDING):
                continue

            if order.symbol not in self.data:
                continue

            # Only one fill per symbol per bar (OCO simulation)
            if order.symbol in filled_symbols:
                continue

            df = self.data[order.symbol]
            idx = self.current_bar_index[order.symbol]

            if idx >= len(df):
                continue

            bar = df.iloc[idx]
            low = Decimal(str(bar["low"]))
            high = Decimal(str(bar["high"]))

            fill_price = None

            # Check fill conditions based on order type
            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY:
                    # Buy limit fills if low <= limit_price
                    if low <= order.limit_price:
                        fill_price = order.limit_price
                else:
                    # Sell limit fills if high >= limit_price
                    if high >= order.limit_price:
                        fill_price = order.limit_price

            elif order.order_type == OrderType.STOP:
                if order.side == OrderSide.BUY:
                    # Buy stop fills if high >= stop_price
                    if high >= order.stop_price:
                        fill_price = order.stop_price
                else:
                    # Sell stop fills if low <= stop_price
                    if low <= order.stop_price:
                        fill_price = order.stop_price

            elif order.order_type == OrderType.TRAILING_STOP:
                # Update high watermark using bar high (not close)
                if order.id in self._trailing_stop_highs:
                    current_high = self._trailing_stop_highs[order.id]
                    if high > current_high:
                        self._trailing_stop_highs[order.id] = high
                        current_high = high

                    # Calculate trail stop price
                    # trail_percent is already in percentage form (e.g., 5.0 for 5%)
                    trail_pct = order.trail_percent / Decimal("100")
                    trail_stop_price = current_high * (Decimal("1") - trail_pct)

                    # Check if stop triggered
                    if low <= trail_stop_price:
                        fill_price = trail_stop_price

            # Fill the order if conditions met
            if fill_price is not None:
                order.status = OrderStatus.FILLED
                order.filled_qty = order.qty
                order.filled_avg_price = fill_price
                filled_symbols.add(order.symbol)

                self._update_position(order)

                self.logger.info(
                    f"{order.order_type.value} order filled: "
                    f"{order.side.value} {order.qty} {order.symbol} @ {fill_price}"
                )

    def _update_position(self, order: Order) -> None:
        """Update positions based on filled order."""
        quote = self.get_quote(order.symbol)
        fill_price = order.filled_avg_price
        current_price = quote.last

        # Update cash
        if order.side == OrderSide.BUY:
            cost = fill_price * order.filled_qty
            self._account.cash -= cost
        else:
            proceeds = fill_price * order.filled_qty
            self._account.cash += proceeds

        # Update position
        if order.symbol in self._positions:
            pos = self._positions[order.symbol]

            if order.side == OrderSide.BUY:
                # Add to position
                new_qty = pos.qty + order.filled_qty
                new_avg = (
                    pos.avg_entry_price * pos.qty + fill_price * order.filled_qty
                ) / new_qty
            else:
                # Reduce position
                new_qty = pos.qty - order.filled_qty
                new_avg = pos.avg_entry_price

            if new_qty > 0:
                self._positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=new_qty,
                    avg_entry_price=new_avg,
                    current_price=current_price,
                    market_value=new_qty * current_price,
                    unrealized_pl=(current_price - new_avg) * new_qty,
                    unrealized_pl_pct=(current_price - new_avg) / new_avg * Decimal("100"),
                )
            else:
                # Position closed
                del self._positions[order.symbol]

        else:
            # New position (must be buy)
            if order.side == OrderSide.BUY:
                self._positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=order.filled_qty,
                    avg_entry_price=fill_price,
                    current_price=current_price,
                    market_value=order.filled_qty * current_price,
                    unrealized_pl=Decimal("0"),
                    unrealized_pl_pct=Decimal("0"),
                )

    def _update_account(self) -> None:
        """Update account equity based on current positions."""
        positions_value = sum(pos.market_value for pos in self._positions.values())

        self._account.equity = self._account.cash + positions_value
        self._account.portfolio_value = self._account.equity
        self._account.buying_power = self._account.cash  # No margin
