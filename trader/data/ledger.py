"""Trade ledger for recording all trades."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from trader.api.broker import OrderSide, OrderStatus


@dataclass
class TradeRecord:
    """Record of a completed trade."""

    id: int
    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: Decimal
    price: Decimal
    total: Decimal
    status: str
    rule_id: Optional[str]
    timestamp: datetime

    @property
    def is_buy(self) -> bool:
        return self.side == "buy"

    @property
    def is_sell(self) -> bool:
        return self.side == "sell"


class TradeLedger:
    """SQLite-backed trade ledger."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize ledger.

        Args:
            db_path: Path to SQLite database. If None, uses default location.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "trades.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    status TEXT NOT NULL,
                    rule_id TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)
            """)
            conn.commit()

    def record_trade(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        status: OrderStatus,
        rule_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """Record a trade.

        Args:
            order_id: Broker order ID.
            symbol: Stock symbol.
            side: Buy or sell.
            quantity: Number of shares.
            price: Execution price.
            status: Order status.
            rule_id: ID of rule that triggered this trade (if any).
            timestamp: Trade timestamp.

        Returns:
            Trade record ID.
        """
        if timestamp is None:
            timestamp = datetime.now()

        total = quantity * price

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO trades (order_id, symbol, side, quantity, price, total, status, rule_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    symbol,
                    side.value,
                    float(quantity),
                    float(price),
                    float(total),
                    status.value,
                    rule_id,
                    timestamp.isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_trades(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[TradeRecord]:
        """Get trade records.

        Args:
            symbol: Filter by symbol.
            since: Filter trades after this time.
            limit: Maximum number of records.

        Returns:
            List of trade records.
        """
        query = "SELECT id, order_id, symbol, side, quantity, price, total, status, rule_id, timestamp FROM trades WHERE 1=1"
        params: list = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            TradeRecord(
                id=row[0],
                order_id=row[1],
                symbol=row[2],
                side=row[3],
                quantity=Decimal(str(row[4])),
                price=Decimal(str(row[5])),
                total=Decimal(str(row[6])),
                status=row[7],
                rule_id=row[8],
                timestamp=datetime.fromisoformat(row[9]),
            )
            for row in rows
        ]

    def get_today_trades(self) -> list[TradeRecord]:
        """Get all trades from today."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_trades(since=today, limit=1000)

    def get_today_pnl(self) -> dict[str, Decimal]:
        """Calculate today's realized P/L by symbol.

        Returns:
            Dict mapping symbol to realized P/L.
        """
        trades = self.get_today_trades()
        pnl: dict[str, Decimal] = {}

        # Track cost basis per symbol
        positions: dict[str, list[tuple[Decimal, Decimal]]] = {}  # symbol -> [(qty, price), ...]

        for trade in sorted(trades, key=lambda t: t.timestamp):
            symbol = trade.symbol

            if symbol not in positions:
                positions[symbol] = []
            if symbol not in pnl:
                pnl[symbol] = Decimal("0")

            if trade.is_buy:
                # Add to position
                positions[symbol].append((trade.quantity, trade.price))
            else:
                # Sell - calculate P/L using FIFO
                remaining = trade.quantity
                while remaining > 0 and positions[symbol]:
                    buy_qty, buy_price = positions[symbol][0]
                    sell_qty = min(remaining, buy_qty)

                    # P/L for this portion
                    pnl[symbol] += sell_qty * (trade.price - buy_price)

                    remaining -= sell_qty
                    if sell_qty >= buy_qty:
                        positions[symbol].pop(0)
                    else:
                        positions[symbol][0] = (buy_qty - sell_qty, buy_price)

        return pnl

    def get_total_today_pnl(self) -> Decimal:
        """Get total realized P/L for today."""
        pnl = self.get_today_pnl()
        return sum(pnl.values(), Decimal("0"))

    def get_trade_count_today(self) -> int:
        """Get number of trades today."""
        return len(self.get_today_trades())

    def export_csv(self, path: Path, since: Optional[datetime] = None) -> int:
        """Export trades to CSV.

        Args:
            path: Output file path.
            since: Export trades after this time.

        Returns:
            Number of records exported.
        """
        trades = self.get_trades(since=since, limit=100000)

        with open(path, "w") as f:
            f.write("id,order_id,symbol,side,quantity,price,total,status,rule_id,timestamp\n")
            for t in trades:
                f.write(
                    f"{t.id},{t.order_id},{t.symbol},{t.side},{t.quantity},{t.price},"
                    f"{t.total},{t.status},{t.rule_id or ''},{t.timestamp.isoformat()}\n"
                )

        return len(trades)
