"""Logging configuration for BareTrader."""

import logging
import sys
from pathlib import Path


def setup_logging(
    log_dir: Path | None = None,
    level: int = logging.INFO,
    log_to_file: bool = True,
    console_stream: object | None = None,
) -> logging.Logger:
    """Set up logging for the application.

    Args:
        log_dir: Directory for log files. If None, only console logging.
        level: Logging level.
        log_to_file: Whether to log to file in addition to console.
        console_stream: Stream for console logging. Defaults to sys.stdout.
            Use sys.stderr for MCP stdio transport to avoid corrupting the
            protocol stream.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("baretrader")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    stream = console_stream if console_stream is not None else sys.stdout
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "baretrader.log")
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        # Separate trade audit log
        trade_handler = logging.FileHandler(log_dir / "trades.log")
        trade_handler.setLevel(logging.INFO)
        trade_format = logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        trade_handler.setFormatter(trade_format)
        trade_logger = logging.getLogger("baretrader.trades")
        trade_logger.addHandler(trade_handler)
        trade_logger.setLevel(logging.INFO)

    return logger


def get_logger(name: str = "baretrader") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
