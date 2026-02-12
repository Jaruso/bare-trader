"""App-layer notification services for CLI and MCP."""

from pathlib import Path
from typing import Any

import yaml

from trader.notifications.formatters import TradeNotification
from trader.notifications.manager import NotificationManager


def _config_dir() -> Path:
    return Path(__file__).parent.parent.parent / "config"


def _load_notifications_config() -> dict[str, Any]:
    """Load optional config/notifications.yaml."""
    path = _config_dir() / "notifications.yaml"
    if not path.is_file():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "notifications" not in data:
        return {}
    return data["notifications"]


def get_notification_manager(config_dir: Path | None = None) -> NotificationManager:
    """Return a NotificationManager with env + optional YAML config."""
    if config_dir is None:
        config_dir = _config_dir()
    config_path = config_dir / "notifications.yaml"
    config: dict[str, Any] = {}
    if config_path.is_file():
        with open(config_path) as f:
            data = yaml.safe_load(f)
        if data and "notifications" in data:
            config = data["notifications"]
    return NotificationManager(config)


def send_notification(
    message: str,
    channel: str | None = None,
    config_dir: Path | None = None,
) -> None:
    """Send a manual notification to configured channel(s).

    Args:
        message: Text to send.
        channel: 'discord', 'webhook', or 'all' (default: all enabled).
        config_dir: Optional config directory for notifications.yaml.
    """
    manager = get_notification_manager(config_dir=config_dir)
    if not manager.enabled:
        return
    if channel and channel != "all":
        ch = manager.get_channel(channel)
        if ch:
            ch.send(message)
    else:
        manager.send("manual", {"message": message})


def send_test_notification(
    channel: str | None = None,
    config_dir: Path | None = None,
) -> bool:
    """Send a test notification. Returns True if at least one channel succeeded."""
    manager = get_notification_manager(config_dir=config_dir)
    if not manager.enabled:
        return False
    msg = "AutoTrader test notification — notifications are working."
    if channel and channel != "all":
        ch = manager.get_channel(channel)
        channels = [ch] if ch else []
    else:
        channels = [manager.get_channel(n) for n in manager.channel_names]
        channels = [c for c in channels if c is not None]
    ok = False
    for ch in channels:
        try:
            ch.send(msg)
            ok = True
        except Exception:
            pass
    return ok


def send_trade_notification(
    trade: TradeNotification,
    config_dir: Path | None = None,
) -> None:
    """Send a trade open/close notification to all enabled channels."""
    manager = get_notification_manager(config_dir=config_dir)
    manager.send_trade(trade)
