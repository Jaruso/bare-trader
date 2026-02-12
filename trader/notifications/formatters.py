"""Message formatting for notification channels."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TradeNotification:
    """Payload for trade open/close notifications."""

    symbol: str
    side: str  # "buy" / "sell"
    quantity: int | float
    price: float
    strategy_name: str
    timestamp: datetime | None = None
    event: str = "trade"  # "trade_opened" | "trade_closed"

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)  # noqa: UP017


def format_trade_plain(trade: TradeNotification) -> str:
    """Plain-text trade message (e.g. for generic webhook)."""
    ts = trade.timestamp.strftime("%Y-%m-%d %H:%M:%S") if trade.timestamp else ""
    icon = "🟢" if trade.side.lower() == "buy" else "🔴"
    action = "Opened" if trade.event == "trade_opened" else "Closed"
    return (
        f"{icon} **{action} - {trade.symbol}**\n"
        f"**Side:** {trade.side.upper()}\n"
        f"**Qty:** {trade.quantity} shares\n"
        f"**Price:** ${trade.price:.2f}\n"
        f"**Strategy:** {trade.strategy_name}\n"
        f"**Time:** {ts}"
    )


def format_trade_discord(trade: TradeNotification) -> str:
    """Discord-friendly trade message (markdown)."""
    return format_trade_plain(trade)


def format_error_plain(error: Exception) -> str:
    """Plain-text error message."""
    return f"⚠️ **Error**\n{type(error).__name__}: {error!s}"
