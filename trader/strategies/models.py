"""Strategy models for automated trading.

This module defines the core data models for trading strategies. Unlike simple
rules that fire once, strategies manage the complete trade lifecycle from
entry to exit.

Strategy Types
--------------
- **Trailing Stop**: Ride trends and lock in gains. Entry at market/limit,
  exit via trailing stop that follows price upward.

- **Bracket**: Defined risk/reward. Entry with both take-profit and stop-loss
  levels. Whichever hits first closes the position.

- **Scale Out**: Capture gains while riding. Buy full position, then sell
  portions at progressive profit targets.

- **Grid**: Profit from sideways volatility. Buy at intervals on the way
  down, sell at intervals on the way up.

Example
-------
    >>> from trader.strategies.models import Strategy, StrategyType
    >>> strategy = Strategy(
    ...     symbol="AAPL",
    ...     strategy_type=StrategyType.TRAILING_STOP,
    ...     quantity=10,
    ...     trailing_stop_pct=Decimal("5.0"),
    ... )
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class StrategyType(Enum):
    """Available trading strategy types.

    Each strategy type implements different entry/exit logic:

    - TRAILING_STOP: Follow price up, sell on reversal
    - BRACKET: Take-profit OR stop-loss (OCO)
    - SCALE_OUT: Sell portions at profit targets
    - GRID: Buy low intervals, sell high intervals
    - PULLBACK_TRAILING: Wait for pullback (X% from high), then buy; manage with trailing stop
    """

    TRAILING_STOP = "trailing_stop"
    BRACKET = "bracket"
    SCALE_OUT = "scale_out"
    GRID = "grid"
    PULLBACK_TRAILING = "pullback_trailing"


class StrategyPhase(Enum):
    """Current phase in the strategy lifecycle.

    State machine flow:

        PENDING -> ENTRY_ACTIVE -> POSITION_OPEN -> EXITING -> COMPLETED
                        |               |              |
                        v               v              v
                      FAILED         FAILED         FAILED

    PAUSED can be entered from any active state.
    """

    PENDING = "pending"              # Waiting for entry condition
    ENTRY_ACTIVE = "entry_active"    # Entry order placed, awaiting fill
    POSITION_OPEN = "position_open"  # Position acquired, managing exit
    EXITING = "exiting"              # Exit order(s) placed, awaiting fill
    COMPLETED = "completed"          # Strategy finished successfully
    FAILED = "failed"                # Strategy failed (order rejected, etc.)
    PAUSED = "paused"                # User paused the strategy


class EntryType(Enum):
    """How to enter the position."""

    MARKET = "market"      # Enter immediately at market price
    LIMIT = "limit"        # Enter at specified limit price
    CONDITION = "condition"  # Enter when price condition is met


@dataclass
class Strategy:
    """A trading strategy that manages entry-to-exit lifecycle.

    Attributes
    ----------
    id : str
        Unique identifier for this strategy.
    symbol : str
        Stock ticker symbol (e.g., "AAPL").
    strategy_type : StrategyType
        The type of strategy (trailing_stop, bracket, etc.).
    phase : StrategyPhase
        Current lifecycle phase.
    quantity : int
        Number of shares to trade.
    enabled : bool
        Whether the strategy is active.

    Entry Configuration
    -------------------
    entry_type : EntryType
        How to enter (market, limit, or condition).
    entry_price : Decimal, optional
        Target price for limit entries.
    entry_condition : str, optional
        Price condition string (e.g., "below:170.00").

    Exit Configuration
    ------------------
    trailing_stop_pct : Decimal, optional
        Trailing stop percentage (for TRAILING_STOP strategy).
    take_profit_pct : Decimal, optional
        Take profit percentage (for BRACKET strategy).
    stop_loss_pct : Decimal, optional
        Stop loss percentage (for BRACKET strategy).
    scale_targets : list, optional
        List of scale-out targets (for SCALE_OUT strategy).
    grid_config : dict, optional
        Grid configuration (for GRID strategy).

    State Tracking
    --------------
    entry_order_id : str, optional
        Broker order ID for entry order.
    entry_fill_price : Decimal, optional
        Actual fill price for entry.
    high_watermark : Decimal, optional
        Highest price since entry (for trailing stop).
    exit_order_ids : list
        Broker order IDs for exit orders.

    Metadata
    --------
    created_at : datetime
        When the strategy was created.
    updated_at : datetime
        When the strategy was last updated.
    notes : str, optional
        User notes about this strategy.
    """

    # Required fields
    symbol: str
    strategy_type: StrategyType
    quantity: int

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Lifecycle
    phase: StrategyPhase = StrategyPhase.PENDING
    enabled: bool = True

    # Entry configuration
    entry_type: EntryType = EntryType.MARKET
    entry_price: Decimal | None = None
    entry_condition: str | None = None

    # Exit configuration - Trailing Stop
    trailing_stop_pct: Decimal | None = None

    # Pullback-Trailing: wait for pullback, then trailing stop exit
    pullback_pct: Decimal | None = None  # e.g. 5 = buy when price drops 5% from reference
    pullback_reference_price: Decimal | None = None  # high-water mark while waiting for pullback

    # Exit configuration - Bracket
    take_profit_pct: Decimal | None = None
    stop_loss_pct: Decimal | None = None

    # Exit configuration - Scale Out
    # Format: [{"pct": 33, "target_pct": 5}, {"pct": 33, "target_pct": 10}, ...]
    scale_targets: list[dict] | None = None

    # Exit configuration - Grid
    # Format: {"low": 380, "high": 420, "levels": 5, "qty_per_level": 10}
    grid_config: dict | None = None

    # State tracking
    entry_order_id: str | None = None
    entry_fill_price: Decimal | None = None
    high_watermark: Decimal | None = None
    exit_order_ids: list[str] = field(default_factory=list)

    # For scale-out: track which tranches have been sold
    # Format: [{"pct": 33, "target_pct": 5, "sold": False, "order_id": None}, ...]
    scale_state: list[dict] | None = None

    # For grid: track grid level states
    # Format: [{"price": 390, "side": "buy", "filled": False, "order_id": None}, ...]
    grid_state: list[dict] | None = None

    # Scheduling
    schedule_at: datetime | None = None  # Schedule strategy to start at this time
    schedule_enabled: bool = False  # Enable scheduling (strategy won't execute until schedule_at)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate strategy after initialization."""
        self.symbol = self.symbol.upper()

        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Validate strategy-specific requirements
        if self.strategy_type == StrategyType.TRAILING_STOP:
            if self.trailing_stop_pct is None:
                raise ValueError("Trailing stop strategy requires trailing_stop_pct")
            if self.trailing_stop_pct <= 0:
                raise ValueError("Trailing stop percentage must be positive")

        elif self.strategy_type == StrategyType.BRACKET:
            if self.take_profit_pct is None or self.stop_loss_pct is None:
                raise ValueError("Bracket strategy requires take_profit_pct and stop_loss_pct")
            if self.take_profit_pct <= 0 or self.stop_loss_pct <= 0:
                raise ValueError("Take profit and stop loss percentages must be positive")

        elif self.strategy_type == StrategyType.SCALE_OUT:
            if self.scale_targets is None or len(self.scale_targets) == 0:
                raise ValueError("Scale out strategy requires scale_targets")
            # Validate targets sum to 100%
            total_pct = sum(t.get("pct", 0) for t in self.scale_targets)
            if total_pct != 100:
                raise ValueError(f"Scale targets must sum to 100%, got {total_pct}%")

        elif self.strategy_type == StrategyType.PULLBACK_TRAILING:
            if self.pullback_pct is None or self.pullback_pct <= 0:
                raise ValueError("Pullback-trailing strategy requires pullback_pct > 0")
            if self.trailing_stop_pct is None or self.trailing_stop_pct <= 0:
                raise ValueError("Pullback-trailing strategy requires trailing_stop_pct > 0")
        elif self.strategy_type == StrategyType.GRID:
            if self.grid_config is None:
                raise ValueError("Grid strategy requires grid_config")
            required_keys = {"low", "high", "levels", "qty_per_level"}
            if not required_keys.issubset(self.grid_config.keys()):
                raise ValueError(f"Grid config requires: {required_keys}")

    def to_dict(self) -> dict:
        """Convert strategy to dictionary for serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "strategy_type": self.strategy_type.value,
            "phase": self.phase.value,
            "quantity": self.quantity,
            "enabled": self.enabled,
            "entry_type": self.entry_type.value,
            "entry_price": str(self.entry_price) if self.entry_price else None,
            "entry_condition": self.entry_condition,
            "trailing_stop_pct": str(self.trailing_stop_pct) if self.trailing_stop_pct else None,
            "pullback_pct": str(self.pullback_pct) if self.pullback_pct else None,
            "pullback_reference_price": str(self.pullback_reference_price) if self.pullback_reference_price else None,
            "take_profit_pct": str(self.take_profit_pct) if self.take_profit_pct else None,
            "stop_loss_pct": str(self.stop_loss_pct) if self.stop_loss_pct else None,
            "scale_targets": self.scale_targets,
            "grid_config": self.grid_config,
            "entry_order_id": self.entry_order_id,
            "entry_fill_price": str(self.entry_fill_price) if self.entry_fill_price else None,
            "high_watermark": str(self.high_watermark) if self.high_watermark else None,
            "exit_order_ids": self.exit_order_ids,
            "scale_state": self.scale_state,
            "grid_state": self.grid_state,
            "schedule_at": self.schedule_at.isoformat() if self.schedule_at else None,
            "schedule_enabled": self.schedule_enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Strategy":
        """Create strategy from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            symbol=data["symbol"],
            strategy_type=StrategyType(data["strategy_type"]),
            phase=StrategyPhase(data.get("phase", "pending")),
            quantity=int(data["quantity"]),
            enabled=data.get("enabled", True),
            entry_type=EntryType(data.get("entry_type", "market")),
            entry_price=Decimal(data["entry_price"]) if data.get("entry_price") else None,
            entry_condition=data.get("entry_condition"),
            trailing_stop_pct=Decimal(data["trailing_stop_pct"]) if data.get("trailing_stop_pct") else None,
            pullback_pct=Decimal(data["pullback_pct"]) if data.get("pullback_pct") else None,
            pullback_reference_price=Decimal(data["pullback_reference_price"]) if data.get("pullback_reference_price") else None,
            take_profit_pct=Decimal(data["take_profit_pct"]) if data.get("take_profit_pct") else None,
            stop_loss_pct=Decimal(data["stop_loss_pct"]) if data.get("stop_loss_pct") else None,
            scale_targets=data.get("scale_targets"),
            grid_config=data.get("grid_config"),
            entry_order_id=data.get("entry_order_id"),
            entry_fill_price=Decimal(data["entry_fill_price"]) if data.get("entry_fill_price") else None,
            high_watermark=Decimal(data["high_watermark"]) if data.get("high_watermark") else None,
            exit_order_ids=data.get("exit_order_ids", []),
            scale_state=data.get("scale_state"),
            grid_state=data.get("grid_state"),
            schedule_at=datetime.fromisoformat(data["schedule_at"]) if data.get("schedule_at") else None,
            schedule_enabled=data.get("schedule_enabled", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            notes=data.get("notes"),
        )

    def update_phase(self, new_phase: StrategyPhase) -> None:
        """Update the strategy phase and timestamp."""
        self.phase = new_phase
        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """Check if strategy is in an active (non-terminal) phase."""
        return self.phase not in (
            StrategyPhase.COMPLETED,
            StrategyPhase.FAILED,
            StrategyPhase.PAUSED,
        )

    def is_terminal(self) -> bool:
        """Check if strategy is in a terminal phase."""
        return self.phase in (StrategyPhase.COMPLETED, StrategyPhase.FAILED)

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "ON" if self.enabled else "OFF"
        phase_icon = {
            StrategyPhase.PENDING: "...",
            StrategyPhase.ENTRY_ACTIVE: "->",
            StrategyPhase.POSITION_OPEN: "$$",
            StrategyPhase.EXITING: "<-",
            StrategyPhase.COMPLETED: "OK",
            StrategyPhase.FAILED: "XX",
            StrategyPhase.PAUSED: "||",
        }.get(self.phase, "??")

        return f"[{status}] [{phase_icon}] {self.strategy_type.value}: {self.quantity} {self.symbol}"
