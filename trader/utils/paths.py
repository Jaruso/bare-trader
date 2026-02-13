"""Centralized path resolution for AutoTrader.

Handles config, data, and log directories for both development and installed environments.
Uses XDG Base Directory spec on Linux, standard locations on macOS/Windows.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


def get_config_dir(custom_path: Path | None = None) -> Path:
    """Get the configuration directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: project root / config (if exists)
    3. Installed mode: ~/.autotrader/config (or XDG_CONFIG_HOME/autotrader on Linux)

    Args:
        custom_path: Optional custom config directory path.

    Returns:
        Path to config directory (created if needed).
    """
    if custom_path:
        config_dir = Path(custom_path)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    # Check if we're in development mode (config dir exists relative to code)
    # Use absolute path resolution to avoid issues with cwd changes
    project_root = Path(__file__).resolve().parent.parent.parent
    dev_config = project_root / "config"
    if dev_config.exists() and (dev_config / "strategies.yaml").exists():
        # Development mode - use project config
        return dev_config

    # Installed mode - use user config directory
    system = platform.system()

    if system == "Linux":
        # XDG Base Directory spec
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "autotrader"
        else:
            config_dir = Path.home() / ".config" / "autotrader"
    elif system == "Darwin":  # macOS
        config_dir = Path.home() / ".autotrader" / "config"
    else:  # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "autotrader" / "config"
        else:
            config_dir = Path.home() / ".autotrader" / "config"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir(custom_path: Path | None = None) -> Path:
    """Get the data directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: project root / data (if exists)
    3. Installed mode: ~/.autotrader/data (or XDG_DATA_HOME/autotrader on Linux)

    Args:
        custom_path: Optional custom data directory path.

    Returns:
        Path to data directory (created if needed).
    """
    if custom_path:
        data_dir = Path(custom_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    # Check if we're in development mode
    project_root = Path(__file__).resolve().parent.parent.parent
    dev_data = project_root / "data"
    if dev_data.exists():
        # Development mode - use project data
        return dev_data

    # Installed mode - use user data directory
    system = platform.system()

    if system == "Linux":
        # XDG Base Directory spec
        xdg_data = os.getenv("XDG_DATA_HOME")
        if xdg_data:
            data_dir = Path(xdg_data) / "autotrader"
        else:
            data_dir = Path.home() / ".local" / "share" / "autotrader"
    elif system == "Darwin":  # macOS
        data_dir = Path.home() / ".autotrader" / "data"
    else:  # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            data_dir = Path(appdata) / "autotrader" / "data"
        else:
            data_dir = Path.home() / ".autotrader" / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir(custom_path: Path | None = None) -> Path:
    """Get the log directory path.

    Priority:
    1. Custom path if provided
    2. Development mode: project root / logs (if exists)
    3. Installed mode: ~/.autotrader/logs (or XDG_STATE_HOME/autotrader on Linux)

    Args:
        custom_path: Optional custom log directory path.

    Returns:
        Path to log directory (created if needed).
    """
    if custom_path:
        log_dir = Path(custom_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    # Check if we're in development mode
    project_root = Path(__file__).resolve().parent.parent.parent
    dev_logs = project_root / "logs"
    if dev_logs.exists():
        # Development mode - use project logs
        return dev_logs

    # Installed mode - use user log directory
    system = platform.system()

    if system == "Linux":
        # XDG Base Directory spec
        xdg_state = os.getenv("XDG_STATE_HOME")
        if xdg_state:
            log_dir = Path(xdg_state) / "autotrader"
        else:
            log_dir = Path.home() / ".local" / "state" / "autotrader"
    elif system == "Darwin":  # macOS
        log_dir = Path.home() / ".autotrader" / "logs"
    else:  # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            log_dir = Path(appdata) / "autotrader" / "logs"
        else:
            log_dir = Path.home() / ".autotrader" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_project_root() -> Path:
    """Get the project root directory.

    Returns project root if in development mode, otherwise None.
    Useful for detecting development vs installed mode.
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    # Check if this looks like a development installation
    if (project_root / "config" / "strategies.yaml").exists():
        return project_root

    # Check if this looks like a development installation (alternative check)
    if (project_root / "pyproject.toml").exists():
        return project_root

    return project_root  # Return anyway, but caller should check if it's valid
