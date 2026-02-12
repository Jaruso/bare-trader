"""Generic HTTP webhook notification channel."""

import logging
from typing import Any

import requests

from trader.notifications.channels.base import NotificationChannel
from trader.notifications.formatters import TradeNotification, format_trade_plain

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    """Send notifications to a generic HTTP webhook (POST JSON body)."""

    def __init__(self, url: str) -> None:
        if not url or not url.strip():
            raise ValueError("Webhook URL is required")
        self.url = url.strip()

    @property
    def name(self) -> str:
        return "webhook"

    def send(self, message: str, **kwargs: Any) -> None:
        """POST JSON body with 'message' and optional 'event'."""
        payload: dict[str, Any] = {"message": message}
        if kwargs.get("event"):
            payload["event"] = str(kwargs["event"])
        try:
            resp = requests.post(
                self.url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Webhook send failed: %s", e)
            raise

    def format_trade(self, trade: TradeNotification) -> str:
        return format_trade_plain(trade)
