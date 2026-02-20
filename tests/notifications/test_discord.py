"""Tests for Discord notification channel."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from trader.notifications.channels.discord import DiscordChannel
from trader.notifications.formatters import TradeNotification


def test_discord_channel_requires_url() -> None:
    """DiscordChannel raises if webhook URL is empty."""
    with pytest.raises(ValueError, match="webhook URL"):
        DiscordChannel("")
    with pytest.raises(ValueError, match="webhook URL"):
        DiscordChannel("   ")


def test_discord_channel_name() -> None:
    """Discord channel name is 'discord'."""
    with patch.object(requests, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=204)
        ch = DiscordChannel("https://discord.com/api/webhooks/123/abc")
    assert ch.name == "discord"


def test_discord_send_posts_json() -> None:
    """Discord send POSTs content to webhook URL."""
    with patch.object(requests, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=204)
        ch = DiscordChannel("https://discord.com/api/webhooks/123/abc")
        ch.send("Hello world")
    mock_post.assert_called_once()
    call_kw = mock_post.call_args[1]
    assert call_kw["json"]["content"] == "Hello world"
    assert "application/json" in str(call_kw["headers"])


def test_discord_send_raises_on_http_error() -> None:
    """Discord send raises on non-2xx response."""
    with patch.object(requests, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=400)
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("400")
        ch = DiscordChannel("https://discord.com/api/webhooks/123/abc")
        with pytest.raises(requests.HTTPError):
            ch.send("fail")


def test_discord_format_trade() -> None:
    """Discord format_trade produces markdown with symbol and strategy."""
    ch = DiscordChannel("https://discord.com/api/webhooks/1/2")
    trade = TradeNotification(
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=150.0,
        strategy_name="trailing-stop",
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
    )
    msg = ch.format_trade(trade)
    assert "AAPL" in msg
    assert "trailing-stop" in msg
    assert "150" in msg
