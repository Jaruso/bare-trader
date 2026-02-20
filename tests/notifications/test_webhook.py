"""Tests for generic webhook channel."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from trader.notifications.channels.webhook import WebhookChannel


def test_webhook_channel_requires_url() -> None:
    """WebhookChannel raises if URL is empty."""
    with pytest.raises(ValueError, match="URL"):
        WebhookChannel("")
    with pytest.raises(ValueError, match="URL"):
        WebhookChannel("   ")


def test_webhook_send_posts_json() -> None:
    """Webhook send POSTs JSON with message and optional event."""
    with patch.object(requests, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        ch = WebhookChannel("https://example.com/webhook")
        ch.send("Test message", event="trade_opened")
    mock_post.assert_called_once()
    call_kw = mock_post.call_args[1]
    assert call_kw["json"]["message"] == "Test message"
    assert call_kw["json"]["event"] == "trade_opened"
