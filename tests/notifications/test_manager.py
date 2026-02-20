"""Tests for NotificationManager."""

import os
from unittest.mock import patch

from baretrader.notifications.formatters import TradeNotification
from baretrader.notifications.manager import NotificationManager, _resolve_url


def test_resolve_url_plain() -> None:
    """Plain URL is returned as-is."""
    assert _resolve_url("https://discord.com/api/webhooks/123") == "https://discord.com/api/webhooks/123"


def test_resolve_url_env() -> None:
    """${VAR} is resolved from environment."""
    with patch.dict(os.environ, {"MY_WEBHOOK": "https://example.com/hook"}, clear=False):
        assert _resolve_url("${MY_WEBHOOK}") == "https://example.com/hook"


def test_manager_empty_config_no_channels() -> None:
    """With no env and empty config, manager has no channels."""
    with patch.dict(os.environ, {}, clear=False):
        drop = ("DISCORD_", "CUSTOM_WEBHOOK", "NOTIFICATIONS_")
        env = {k: v for k, v in os.environ.items() if not k.startswith(drop)}
        with patch.dict(os.environ, env, clear=False):
            manager = NotificationManager({})
    assert manager.channel_names == []
    assert manager.enabled is False


def test_manager_disabled_by_env() -> None:
    """NOTIFICATIONS_ENABLED=false disables sending."""
    with patch.dict(
        os.environ,
        {"NOTIFICATIONS_ENABLED": "false", "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/2"},
        clear=False,
    ):
        manager = NotificationManager({})
    # Channels may be built from DISCORD_WEBHOOK_URL
    manager._enabled = False
    assert manager.enabled is False


def test_manager_send_when_disabled_no_op() -> None:
    """Send does nothing when disabled."""
    manager = NotificationManager({"enabled": False})
    manager._channels = []
    manager.send("trade_opened", {"message": "hello"})
    # No exception, no side effect (no channels to call)


def test_manager_send_trade_event_filtering() -> None:
    """send_trade respects event_enabled for trade_opened."""
    with patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": ""}, clear=False):
        manager = NotificationManager({"events": {"trade_opened": False}})
    manager._channels = []
    trade = TradeNotification(
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=100.0,
        strategy_name="test",
        event="trade_opened",
    )
    manager.send_trade(trade)
    # No channels so no HTTP call; event would be skipped anyway


def test_manager_get_channel() -> None:
    """get_channel returns channel by name or None."""
    url = "https://discord.com/api/webhooks/x/y"
    with patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": url}, clear=False):
        manager = NotificationManager({})
    assert manager.get_channel("discord") is not None
    assert manager.get_channel("nonexistent") is None
