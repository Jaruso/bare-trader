"""Trading engine - main execution loop."""

import fcntl
import os
import signal
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

from trader.api.broker import Broker
from trader.strategies.evaluator import StrategyEvaluator
from trader.strategies.loader import get_active_strategies
from trader.utils.config import StrategyDefaults
from trader.utils.logging import get_logger
from trader.oms.store import load_orders, save_order
from trader.models.order import OrderStatus as LocalOrderStatus


class EngineAlreadyRunningError(Exception):
    """Raised when another engine instance is already running."""

    pass


def get_lock_file_path() -> Path:
    """Get the path to the engine lock file."""
    # Store in config directory alongside strategies.yaml
    config_dir = Path(__file__).parent.parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / ".engine.lock"


class TradingEngine:
    """Main trading engine that runs the evaluation loop."""

    def __init__(
        self,
        broker: Broker,
        poll_interval: int = 60,
        dry_run: bool = False,
        orders_dir: Optional[Path] = None,
        strategy_defaults: Optional[StrategyDefaults] = None,
    ) -> None:
        """Initialize trading engine.

        Args:
            broker: Broker instance.
            poll_interval: Seconds between price checks.
            dry_run: If True, don't execute real trades.
            orders_dir: Optional custom orders directory.
            strategy_defaults: Default strategy parameters.
        """
        self.broker = broker
        self.poll_interval = poll_interval
        self.dry_run = dry_run

        # Strategy evaluator
        defaults = strategy_defaults or StrategyDefaults()
        self.strategy_evaluator = StrategyEvaluator(broker, defaults)

        self.logger = get_logger("autotrader.engine")
        self._running = False
        self._stop_requested = False
        self.orders_dir = orders_dir
        self._lock_file = None
        self._lock_fd = None

    def _acquire_lock(self) -> None:
        """Acquire exclusive lock to prevent multiple engine instances.

        Raises:
            EngineAlreadyRunningError: If another engine is already running.
        """
        lock_path = get_lock_file_path()
        self._lock_file = lock_path

        try:
            # Open (or create) the lock file
            self._lock_fd = open(lock_path, "w")

            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID to lock file for debugging
            self._lock_fd.write(str(os.getpid()))
            self._lock_fd.flush()

            self.logger.debug(f"Acquired engine lock: {lock_path}")

        except BlockingIOError:
            # Another process holds the lock
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None

            # Try to read the PID of the other process
            try:
                with open(lock_path) as f:
                    other_pid = f.read().strip()
                raise EngineAlreadyRunningError(
                    f"Another trading engine is already running (PID: {other_pid}). "
                    "Stop it first or use --force to override."
                )
            except FileNotFoundError:
                raise EngineAlreadyRunningError(
                    "Another trading engine is already running."
                )

    def _release_lock(self) -> None:
        """Release the engine lock."""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self.logger.debug("Released engine lock")
            except Exception as e:
                self.logger.warning(f"Error releasing lock: {e}")
            finally:
                self._lock_fd = None

        # Clean up lock file
        if self._lock_file and self._lock_file.exists():
            try:
                self._lock_file.unlink()
            except Exception:
                pass

    def start(self) -> None:
        """Start the trading engine loop.

        Raises:
            EngineAlreadyRunningError: If another engine is already running.
        """
        # Acquire lock to ensure only one engine runs at a time
        self._acquire_lock()

        self._running = True
        self._stop_requested = False

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self.logger.info(
            f"Trading engine started | Poll interval: {self.poll_interval}s | "
            f"Dry run: {self.dry_run}"
        )

        # Reconcile any persisted orders with broker state before starting
        try:
            self._reconcile_orders()
        except Exception as e:
            self.logger.error(f"Error reconciling orders on start: {e}")

        try:
            self._run_loop()
        finally:
            self._running = False
            self._release_lock()
            self.logger.info("Trading engine stopped")

    def _reconcile_orders(self) -> None:
        """Load locally persisted orders and reconcile status with broker."""
        orders = load_orders(self.orders_dir)
        if not orders:
            return

        for o in orders:
            # Only reconcile non-final statuses
            if o.status in (LocalOrderStatus.FILLED, LocalOrderStatus.CANCELED):
                continue

            try:
                broker_order = self.broker.get_order(o.external_id or o.id)
                if not broker_order:
                    continue

                # If status changed, persist updated broker order
                if getattr(broker_order, "status", None) and broker_order.status.value != o.status.value:
                    save_order(broker_order, self.orders_dir)
                    self.logger.info(f"Reconciled order {o.id} -> {broker_order.status.value}")

            except Exception as e:
                self.logger.debug(f"Failed to reconcile order {o.id}: {e}")

    def stop(self) -> None:
        """Request engine stop."""
        self._stop_requested = True
        self.logger.info("Stop requested, will exit after current cycle")

    def _handle_shutdown(self, signum: int, frame: Optional[object]) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def _run_loop(self) -> None:
        """Main trading loop."""
        while not self._stop_requested:
            cycle_start = time.time()

            try:
                self._run_cycle()
            except Exception as e:
                self.logger.error(f"Error in trading cycle: {e}")

            # Sleep until next interval
            elapsed = time.time() - cycle_start
            sleep_time = max(0, self.poll_interval - elapsed)

            if sleep_time > 0 and not self._stop_requested:
                time.sleep(sleep_time)

    def _run_cycle(self) -> None:
        """Run a single evaluation cycle."""
        # Check if market is open
        if not self.broker.is_market_open():
            self.logger.debug("Market closed, skipping cycle")
            return

        # Evaluate strategies
        strategies = get_active_strategies()
        if strategies:
            self.logger.debug(f"Evaluating {len(strategies)} active strategies")
            strategy_ids = self.strategy_evaluator.run_once(strategies, dry_run=self.dry_run)
            if strategy_ids:
                self.logger.info(f"Strategy actions executed: {strategy_ids}")
        else:
            self.logger.debug("No active strategies")

    def run_once(self) -> list[str]:
        """Run a single evaluation cycle manually.

        Returns:
            List of strategy IDs from executed trades.
        """
        self.logger.info("Running single evaluation cycle")

        if not self.broker.is_market_open():
            self.logger.warning("Market is closed")
            return []

        # Run strategies
        strategies = get_active_strategies()
        if strategies:
            return self.strategy_evaluator.run_once(strategies, dry_run=self.dry_run)

        return []

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running
