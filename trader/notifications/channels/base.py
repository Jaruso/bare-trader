"""Base notification channel."""

from abc import ABC, abstractmethod

from trader.notifications.formatters import TradeNotification


class NotificationChannel(ABC):
    """Base class for notification channels."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel identifier (e.g. 'discord', 'webhook')."""
        ...

    @abstractmethod
    def send(self, message: str, **kwargs: object) -> None:
        """Send a text message through this channel."""
        ...

    def format_trade(self, trade: TradeNotification) -> str:
        """Format trade for this channel. Override for channel-specific formatting."""
        from trader.notifications.formatters import format_trade_plain
        return format_trade_plain(trade)
