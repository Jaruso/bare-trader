"""Discord webhook notification channel."""

import logging
from typing import Any

import requests

from trader.notifications.channels.base import NotificationChannel
from trader.notifications.formatters import TradeNotification, format_trade_discord

logger = logging.getLogger(__name__)


class DiscordChannel(NotificationChannel):
    """Send notifications via Discord webhook."""

    def __init__(self, webhook_url: str) -> None:
        if not webhook_url or not webhook_url.strip():
            raise ValueError("Discord webhook URL is required")
        self.webhook_url = webhook_url.strip()

    @property
    def name(self) -> str:
        return "discord"

    def send(self, message: str, **kwargs: Any) -> None:
        """Send message via Discord webhook API."""
        payload: dict[str, Any] = {"content": message[:2000]}
        if kwargs.get("username"):
            payload["username"] = str(kwargs["username"])
        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Discord webhook send failed: %s", e)
            raise

    def format_trade(self, trade: TradeNotification) -> str:
        return format_trade_discord(trade)
