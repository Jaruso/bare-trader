"""Notification manager: routes events to configured channels."""

import logging
import os
from typing import Any

from baretrader.notifications.channels.base import NotificationChannel
from baretrader.notifications.channels.discord import DiscordChannel
from baretrader.notifications.channels.webhook import WebhookChannel
from baretrader.notifications.formatters import TradeNotification, format_error_plain

logger = logging.getLogger(__name__)

DEFAULT_EVENTS = {
    "trade_opened": True,
    "trade_closed": True,
    "strategy_started": True,
    "strategy_stopped": True,
    "error": True,
    "daily_summary": True,
}


def _resolve_url(value: str) -> str:
    """Resolve ${VAR} in config from environment."""
    if not value:
        return value
    s = value.strip()
    if s.startswith("${") and s.endswith("}"):
        var = s[2:-1].strip()
        return os.getenv(var, "")
    return s


def _build_channels(config: dict[str, Any]) -> list[NotificationChannel]:
    """Build list of enabled channels from config."""
    channels: list[NotificationChannel] = []
    # Env override: Discord
    discord_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    channels_cfg = config.get("channels") or {}
    discord_cfg = channels_cfg.get("discord") or {}
    if discord_cfg.get("enabled", True) and (discord_url or discord_cfg.get("webhook_url")):
        url = discord_url or _resolve_url(str(discord_cfg.get("webhook_url", "")))
        if url:
            try:
                channels.append(DiscordChannel(url))
            except ValueError as e:
                logger.warning("Skip Discord channel: %s", e)
    # Generic webhook
    webhook_url = os.getenv("CUSTOM_WEBHOOK_URL", "").strip()
    webhook_cfg = channels_cfg.get("webhook") or {}
    if webhook_cfg.get("enabled", False) or webhook_url:
        url = webhook_url or _resolve_url(str(webhook_cfg.get("url", "")))
        if url:
            try:
                channels.append(WebhookChannel(url))
            except ValueError as e:
                logger.warning("Skip webhook channel: %s", e)
    return channels


class NotificationManager:
    """Manages notification delivery across channels."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Load notification channels from config (and env).

        Config may contain:
        - enabled: bool
        - events: dict of event_name -> bool
        - channels: dict with discord/webhook settings
        """
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        if os.getenv("NOTIFICATIONS_ENABLED", "").lower() in ("0", "false", "no"):
            self._enabled = False
        self._events = {**DEFAULT_EVENTS, **(self._config.get("events") or {})}
        self._channels = _build_channels(self._config)

    @property
    def enabled(self) -> bool:
        return self._enabled and len(self._channels) > 0

    @property
    def channel_names(self) -> list[str]:
        return [c.name for c in self._channels]

    def get_channel(self, name: str) -> NotificationChannel | None:
        """Return channel by name, or None."""
        for c in self._channels:
            if c.name == name:
                return c
        return None

    def _event_enabled(self, event: str) -> bool:
        return bool(self._events.get(event, True))

    def _send_to_all(self, message: str, event: str | None = None) -> None:
        if not self.enabled:
            return
        for ch in self._channels:
            try:
                ch.send(message, event=event)
            except Exception as e:
                logger.warning("Notification channel %s failed: %s", ch.name, e)

    def send(self, event: str, data: dict[str, Any]) -> None:
        """Send notification to all enabled channels.

        Events: trade_opened, trade_closed, strategy_started, strategy_stopped,
        error, daily_summary.
        """
        if not self._enabled or not self._event_enabled(event):
            return
        message = data.get("message") or str(data)
        self._send_to_all(message, event=event)

    def send_trade(self, trade: TradeNotification) -> None:
        """Format and send trade notification to all channels."""
        if not self._enabled or not self._event_enabled(trade.event):
            return
        for ch in self._channels:
            try:
                msg = ch.format_trade(trade)
                ch.send(msg, event=trade.event)
            except Exception as e:
                logger.warning("Notification channel %s failed: %s", ch.name, e)

    def send_error(self, error: Exception) -> None:
        """Format and send error notification."""
        if not self._enabled or not self._event_enabled("error"):
            return
        message = format_error_plain(error)
        self._send_to_all(message, event="error")
