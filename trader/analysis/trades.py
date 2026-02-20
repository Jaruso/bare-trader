"""Trade analysis helpers."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trader.data.ledger import TradeRecord


@dataclass
class TradePnL:
    """Matched buy/sell lot with realized P/L."""

    symbol: str
    quantity: Decimal
    buy_price: Decimal
    sell_price: Decimal
    pnl: Decimal
    buy_time: datetime
    sell_time: datetime
    holding_minutes: Decimal


@dataclass
class TradeStats:
    """Aggregated trade performance statistics."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal
    profit_factor: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    avg_hold_minutes: Decimal


@dataclass
class OpenPosition:
    """Open lot summary from unmatched buys."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    lots: int


@dataclass
class TradeAnalysisReport:
    """Full trade analysis report."""

    summary: TradeStats
    per_symbol: dict[str, TradeStats]
    open_positions: list[OpenPosition]
    unmatched_sell_qty: dict[str, Decimal]


@dataclass
class _Lot:
    quantity: Decimal
    price: Decimal
    timestamp: datetime


def analyze_trades(trades: Iterable[TradeRecord]) -> TradeAnalysisReport:
    """Analyze trades and compute performance statistics.

    Args:
        trades: Iterable of trade records.

    Returns:
        Trade analysis report with summary and per-symbol stats.
    """
    ordered = sorted(trades, key=lambda t: t.timestamp)
    trade_pnls, open_lots, unmatched_sells = _build_trade_pnls(ordered)

    summary = _summarize_pnls(trade_pnls)

    per_symbol: dict[str, list[TradePnL]] = {}
    for pnl in trade_pnls:
        per_symbol.setdefault(pnl.symbol, []).append(pnl)

    per_symbol_stats = {symbol: _summarize_pnls(pnls) for symbol, pnls in per_symbol.items()}

    open_positions = []
    for symbol, lots in open_lots.items():
        total_qty = sum((lot.quantity for lot in lots), Decimal("0"))
        total_cost = sum((lot.quantity * lot.price for lot in lots), Decimal("0"))
        avg_cost = (total_cost / total_qty) if total_qty > 0 else Decimal("0")
        open_positions.append(
            OpenPosition(
                symbol=symbol,
                quantity=total_qty,
                avg_cost=avg_cost,
                lots=len(lots),
            )
        )

    open_positions.sort(key=lambda p: p.symbol)

    return TradeAnalysisReport(
        summary=summary,
        per_symbol=per_symbol_stats,
        open_positions=open_positions,
        unmatched_sell_qty=unmatched_sells,
    )


def _build_trade_pnls(
    trades: list[TradeRecord],
) -> tuple[list[TradePnL], dict[str, list[_Lot]], dict[str, Decimal]]:
    positions: dict[str, list[_Lot]] = {}
    pnls: list[TradePnL] = []
    unmatched_sells: dict[str, Decimal] = {}

    for trade in trades:
        symbol = trade.symbol
        positions.setdefault(symbol, [])
        unmatched_sells.setdefault(symbol, Decimal("0"))

        if trade.is_buy:
            positions[symbol].append(
                _Lot(
                    quantity=trade.quantity,
                    price=trade.price,
                    timestamp=trade.timestamp,
                )
            )
            continue

        remaining = trade.quantity
        while remaining > 0:
            if not positions[symbol]:
                unmatched_sells[symbol] += remaining
                break

            lot = positions[symbol][0]
            matched_qty = remaining if remaining <= lot.quantity else lot.quantity
            pnl = matched_qty * (trade.price - lot.price)
            holding_minutes = Decimal(
                str((trade.timestamp - lot.timestamp).total_seconds() / 60)
            )

            pnls.append(
                TradePnL(
                    symbol=symbol,
                    quantity=matched_qty,
                    buy_price=lot.price,
                    sell_price=trade.price,
                    pnl=pnl,
                    buy_time=lot.timestamp,
                    sell_time=trade.timestamp,
                    holding_minutes=holding_minutes,
                )
            )

            remaining -= matched_qty
            if matched_qty >= lot.quantity:
                positions[symbol].pop(0)
            else:
                lot.quantity -= matched_qty

    return pnls, positions, unmatched_sells


def _summarize_pnls(pnls: list[TradePnL]) -> TradeStats:
    total_trades = len(pnls)
    winning = [pnl.pnl for pnl in pnls if pnl.pnl > 0]
    losing = [pnl.pnl for pnl in pnls if pnl.pnl < 0]

    winning_trades = len(winning)
    losing_trades = len(losing)

    win_rate = (
        (Decimal(winning_trades) / Decimal(total_trades)) * Decimal("100")
        if total_trades > 0
        else Decimal("0")
    )

    gross_profit = sum(winning, Decimal("0"))
    gross_loss = abs(sum(losing, Decimal("0")))
    net_profit = gross_profit - gross_loss

    avg_win = (gross_profit / Decimal(winning_trades)) if winning_trades > 0 else Decimal("0")
    avg_loss = (sum(losing, Decimal("0")) / Decimal(losing_trades)) if losing_trades > 0 else Decimal("0")

    largest_win = max(winning) if winning else Decimal("0")
    largest_loss = min(losing) if losing else Decimal("0")

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else Decimal("0")

    avg_hold_minutes = (
        sum((pnl.holding_minutes for pnl in pnls), Decimal("0")) / Decimal(total_trades)
        if total_trades > 0
        else Decimal("0")
    )

    return TradeStats(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
        avg_hold_minutes=avg_hold_minutes,
    )
