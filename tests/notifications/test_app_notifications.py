"""Tests for app notification services."""

import os
from pathlib import Path
from unittest.mock import patch

from trader.app.notifications import (
    get_notification_manager,
    send_notification,
    send_test_notification,
)

_ENV_KEYS_TO_DROP = ("DISCORD_WEBHOOK_URL", "CUSTOM_WEBHOOK_URL", "NOTIFICATIONS_ENABLED")


def test_get_notification_manager_no_config() -> None:
    """Manager from empty config dir has no channels if no env."""
    with patch.dict(os.environ, {}, clear=False):
        env_clean = {k: v for k, v in os.environ.items() if k not in _ENV_KEYS_TO_DROP}
        with patch.dict(os.environ, env_clean, clear=False):
            manager = get_notification_manager(config_dir=Path("/nonexistent"))
    assert not manager.enabled


def test_send_test_notification_no_channels_returns_false() -> None:
    """send_test_notification returns False when no channels."""
    with patch.dict(os.environ, {}, clear=False):
        env_clean = {k: v for k, v in os.environ.items() if k not in _ENV_KEYS_TO_DROP}
        with patch.dict(os.environ, env_clean, clear=False):
            ok = send_test_notification(config_dir=Path("/nonexistent"))
    assert ok is False


def test_send_notification_no_channels_no_op() -> None:
    """send_notification does nothing when no channels configured."""
    with patch.dict(os.environ, {}, clear=False):
        env_clean = {k: v for k, v in os.environ.items() if k not in _ENV_KEYS_TO_DROP}
        with patch.dict(os.environ, env_clean, clear=False):
            send_notification("hello", config_dir=Path("/nonexistent"))
    # No exception
