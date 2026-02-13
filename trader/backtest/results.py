"""Backtest results and metrics calculation."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from trader.api.broker import Order, OrderSide


@dataclass
class BacktestResult:
    """Results from a backtest run."""

    # Metadata
    id: str
    strategy_type: str
    symbol: str
    start_date: datetime
    end_date: datetime
    created_at: datetime

    # Configuration
    strategy_config: dict
    initial_capital: Decimal

    # Performance Metrics
    total_return: Decimal  # Absolute return in $
    total_return_pct: Decimal  # Return as %
    win_rate: Decimal  # % of winning trades
    profit_factor: Decimal  # Gross profit / Gross loss
    max_drawdown: Decimal  # Maximum peak-to-trough decline in $
    max_drawdown_pct: Decimal  # Max drawdown as %
    sharpe_ratio: Decimal | None = None  # Risk-adjusted return

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")

    # Time Series Data
    equity_curve: list[tuple[datetime, Decimal]] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "id": self.id,
            "strategy_type": self.strategy_type,
            "symbol": self.symbol,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "strategy_config": self.strategy_config,
            "initial_capital": str(self.initial_capital),
            "total_return": str(self.total_return),
            "total_return_pct": str(self.total_return_pct),
            "win_rate": str(self.win_rate),
            "profit_factor": str(self.profit_factor),
            "max_drawdown": str(self.max_drawdown),
            "max_drawdown_pct": str(self.max_drawdown_pct),
            "sharpe_ratio": str(self.sharpe_ratio) if self.sharpe_ratio else None,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": str(self.avg_win),
            "avg_loss": str(self.avg_loss),
            "largest_win": str(self.largest_win),
            "largest_loss": str(self.largest_loss),
            "equity_curve": [
                (ts.isoformat(), str(equity)) for ts, equity in self.equity_curve
            ],
            "trades": self.trades,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BacktestResult":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            strategy_type=data["strategy_type"],
            symbol=data["symbol"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            strategy_config=data["strategy_config"],
            initial_capital=Decimal(data["initial_capital"]),
            total_return=Decimal(data["total_return"]),
            total_return_pct=Decimal(data["total_return_pct"]),
            win_rate=Decimal(data["win_rate"]),
            profit_factor=Decimal(data["profit_factor"]),
            max_drawdown=Decimal(data["max_drawdown"]),
            max_drawdown_pct=Decimal(data["max_drawdown_pct"]),
            sharpe_ratio=Decimal(data["sharpe_ratio"]) if data.get("sharpe_ratio") else None,
            total_trades=data["total_trades"],
            winning_trades=data["winning_trades"],
            losing_trades=data["losing_trades"],
            avg_win=Decimal(data["avg_win"]),
            avg_loss=Decimal(data["avg_loss"]),
            largest_win=Decimal(data["largest_win"]),
            largest_loss=Decimal(data["largest_loss"]),
            equity_curve=[
                (datetime.fromisoformat(ts), Decimal(equity))
                for ts, equity in data["equity_curve"]
            ],
            trades=data["trades"],
        )


def calculate_metrics(
    filled_orders: list[Order],
    equity_curve: list[tuple[datetime, Decimal]],
    initial_capital: Decimal,
    strategy_type: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    strategy_config: dict,
) -> BacktestResult:
    """Calculate backtest metrics from orders and equity curve.

    Args:
        filled_orders: List of all filled orders.
        equity_curve: Time series of (timestamp, equity) tuples.
        initial_capital: Starting capital.
        strategy_type: Type of strategy.
        symbol: Trading symbol.
        start_date: Backtest start date.
        end_date: Backtest end date.
        strategy_config: Strategy configuration dict.

    Returns:
        BacktestResult with calculated metrics.
    """
    # Calculate total return
    final_equity = equity_curve[-1][1] if equity_curve else initial_capital
    total_return = final_equity - initial_capital
    total_return_pct = (total_return / initial_capital) * Decimal("100")

    # Match buy/sell orders to calculate P/L per trade
    trade_pnls = _calculate_trade_pnls(filled_orders)

    # Calculate trade statistics
    winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
    losing_trades = [pnl for pnl in trade_pnls if pnl < 0]

    total_trades = len(trade_pnls)
    num_winning = len(winning_trades)
    num_losing = len(losing_trades)

    win_rate = (
        (Decimal(num_winning) / Decimal(total_trades)) * Decimal("100")
        if total_trades > 0
        else Decimal("0")
    )

    avg_win = (
        sum(winning_trades, Decimal("0")) / Decimal(num_winning)
        if num_winning > 0
        else Decimal("0")
    )

    avg_loss = (
        sum(losing_trades, Decimal("0")) / Decimal(num_losing)
        if num_losing > 0
        else Decimal("0")
    )

    largest_win = max(winning_trades) if winning_trades else Decimal("0")
    largest_loss = min(losing_trades) if losing_trades else Decimal("0")

    # Calculate profit factor
    gross_profit = sum(winning_trades, Decimal("0"))
    gross_loss = abs(sum(losing_trades, Decimal("0")))
    profit_factor = (
        gross_profit / gross_loss if gross_loss > 0 else Decimal("0")
    ).normalize()

    # Ensure clean zero display (avoid "0E+6" artifacts)
    if profit_factor == 0:
        profit_factor = Decimal("0")

    # Calculate maximum drawdown
    max_drawdown, max_drawdown_pct = _calculate_max_drawdown(equity_curve, initial_capital)

    # Convert orders to trade dicts
    trades = [
        {
            "id": order.id,
            "timestamp": order.created_at,
            "symbol": order.symbol,
            "side": order.side.value,
            "qty": str(order.qty),
            "price": str(order.filled_avg_price),
            "total": str(order.qty * order.filled_avg_price),
        }
        for order in filled_orders
    ]

    return BacktestResult(
        id=str(uuid.uuid4())[:8],
        strategy_type=strategy_type,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        created_at=datetime.now(),
        strategy_config=strategy_config,
        initial_capital=initial_capital,
        total_return=total_return,
        total_return_pct=total_return_pct,
        win_rate=win_rate,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=None,  # TODO: Calculate Sharpe ratio
        total_trades=total_trades,
        winning_trades=num_winning,
        losing_trades=num_losing,
        avg_win=avg_win,
        avg_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
        equity_curve=equity_curve,
        trades=trades,
    )


def _calculate_trade_pnls(filled_orders: list[Order]) -> list[Decimal]:
    """Calculate P/L for each trade by matching buys and sells.

    Uses FIFO (First In, First Out) to match orders.

    Args:
        filled_orders: List of filled orders.

    Returns:
        List of P/L values (one per complete trade).
    """
    # Separate buys and sells
    buys = [o for o in filled_orders if o.side == OrderSide.BUY]
    sells = [o for o in filled_orders if o.side == OrderSide.SELL]

    # Match buys to sells using FIFO
    pnls = []
    buy_queue = list(buys)  # Copy to avoid modifying original

    for sell in sells:
        if not buy_queue:
            break

        # Match with first buy
        buy = buy_queue.pop(0)

        # Calculate P/L
        buy_cost = buy.filled_avg_price * buy.qty
        sell_proceeds = sell.filled_avg_price * sell.qty
        pnl = sell_proceeds - buy_cost

        pnls.append(pnl)

    return pnls


def _calculate_max_drawdown(
    equity_curve: list[tuple[datetime, Decimal]], initial_capital: Decimal
) -> tuple[Decimal, Decimal]:
    """Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of (timestamp, equity) tuples.
        initial_capital: Starting capital.

    Returns:
        Tuple of (max_drawdown in $, max_drawdown as %).
    """
    if not equity_curve:
        return Decimal("0"), Decimal("0")

    max_equity = initial_capital
    max_drawdown = Decimal("0")

    for _, equity in equity_curve:
        # Update peak
        if equity > max_equity:
            max_equity = equity

        # Calculate drawdown from peak
        drawdown = max_equity - equity

        # Update max drawdown
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Calculate percentage
    max_drawdown_pct = (
        (max_drawdown / max_equity) * Decimal("100") if max_equity > 0 else Decimal("0")
    )

    # Ensure clean zero display
    if max_drawdown == 0:
        max_drawdown = Decimal("0")
    if max_drawdown_pct == 0:
        max_drawdown_pct = Decimal("0")

    return max_drawdown, max_drawdown_pct
