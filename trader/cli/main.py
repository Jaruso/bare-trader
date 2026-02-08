"""CLI entry point for AutoTrader."""

import click
from rich.console import Console
from rich.table import Table

from decimal import Decimal
from typing import Optional

from datetime import datetime
from pathlib import Path

from trader import __version__
from trader.api.alpaca import AlpacaBroker
from trader.api.broker import Broker, OrderSide, OrderStatus, OrderType
from trader.core.engine import TradingEngine, EngineAlreadyRunningError, get_lock_file_path
from trader.core.portfolio import Portfolio
from trader.core.safety import SafetyCheck, SafetyLimits
from trader.data.ledger import TradeLedger
from trader.oms.store import save_order, load_orders
from trader.utils.config import Config, Environment, load_config
from trader.utils.logging import get_logger, setup_logging

console = Console()


def get_broker(config: Config) -> Broker:
    """Create broker instance from config."""
    return AlpacaBroker(
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key,
        paper=config.is_paper,
    )


@click.group()
@click.version_option(version=__version__, prog_name="trader")
@click.option("--prod", is_flag=True, help="Use production environment (default: paper)")
@click.pass_context
def cli(ctx: click.Context, prod: bool) -> None:
    """AutoTrader - CLI-based automated trading system."""
    ctx.ensure_object(dict)
    config = load_config(prod=prod)
    ctx.obj["config"] = config

    # Set up logging
    logger = setup_logging(log_dir=config.log_dir, log_to_file=True)
    ctx.obj["logger"] = logger


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current system status including engine state."""
    import os

    config = ctx.obj["config"]

    table = Table(title="AutoTrader Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Environment info
    env_style = "yellow" if config.env == Environment.PAPER else "red bold"
    table.add_row("Environment", f"[{env_style}]{config.env.value.upper()}[/{env_style}]")
    table.add_row("Service", config.service.value)
    table.add_row("Base URL", config.base_url)

    # API key status
    key_status = "Configured" if config.alpaca_api_key else "[red]Not Set[/red]"
    table.add_row("API Key", key_status)

    # Engine status
    lock_path = get_lock_file_path()
    engine_running = False
    engine_pid = None

    if lock_path.exists():
        try:
            with open(lock_path) as f:
                pid_str = f.read().strip()
                if pid_str:
                    pid = int(pid_str)
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        engine_running = True
                        engine_pid = pid
                    except ProcessLookupError:
                        pass  # Stale lock file
        except (ValueError, FileNotFoundError):
            pass

    if engine_running:
        table.add_row("Engine", f"[green]RUNNING[/green] (PID {engine_pid})")
    else:
        table.add_row("Engine", "[yellow]NOT RUNNING[/yellow]")

    console.print(table)


@cli.command()
@click.pass_context
def balance(ctx: click.Context) -> None:
    """Show account balance and portfolio summary."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        console.print("Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env")
        return

    try:
        broker = get_broker(config)
        account = broker.get_account()
        positions_list = broker.get_positions()
        market_open = broker.is_market_open()

        # Account table
        table = Table(title="Account Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Portfolio Value", f"${account.portfolio_value:,.2f}")
        table.add_row("Equity", f"${account.equity:,.2f}")
        table.add_row("Cash", f"${account.cash:,.2f}")
        table.add_row("Buying Power", f"${account.buying_power:,.2f}")

        # Day's change
        if account.last_equity:
            day_change = account.equity - account.last_equity
            day_change_pct = (day_change / account.last_equity) * 100 if account.last_equity else 0
            change_style = "green" if day_change >= 0 else "red"
            sign = "+" if day_change >= 0 else ""
            table.add_row(
                "Day's Change",
                f"[{change_style}]{sign}${day_change:,.2f} ({sign}{day_change_pct:.2f}%)[/{change_style}]"
            )

        # Positions summary
        if positions_list:
            total_unrealized = sum(p.unrealized_pl for p in positions_list)
            pl_style = "green" if total_unrealized >= 0 else "red"
            sign = "+" if total_unrealized >= 0 else ""
            table.add_row("Unrealized P/L", f"[{pl_style}]{sign}${total_unrealized:,.2f}[/{pl_style}]")
            table.add_row("Open Positions", str(len(positions_list)))

        table.add_row("", "")  # Spacer
        market_status = "[green]OPEN[/green]" if market_open else "[yellow]CLOSED[/yellow]"
        table.add_row("Market", market_status)
        table.add_row("Day Trades (5d)", str(account.daytrade_count))
        if account.pattern_day_trader:
            table.add_row("PDT Status", "[red]FLAGGED[/red]")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching balance: {e}[/red]")


@cli.command()
@click.pass_context
def positions(ctx: click.Context) -> None:
    """Show current positions."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        positions_list = broker.get_positions()

        if not positions_list:
            console.print("[yellow]No open positions[/yellow]")
            return

        table = Table(title="Open Positions")
        table.add_column("Symbol", style="cyan")
        table.add_column("Qty", justify="right")
        table.add_column("Avg Price", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("Market Value", justify="right")
        table.add_column("P/L", justify="right")
        table.add_column("P/L %", justify="right")

        for pos in positions_list:
            pl_style = "green" if pos.unrealized_pl >= 0 else "red"
            table.add_row(
                pos.symbol,
                str(pos.qty),
                f"${pos.avg_entry_price:,.2f}",
                f"${pos.current_price:,.2f}",
                f"${pos.market_value:,.2f}",
                f"[{pl_style}]${pos.unrealized_pl:,.2f}[/{pl_style}]",
                f"[{pl_style}]{pos.unrealized_pl_pct:.2%}[/{pl_style}]",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching positions: {e}[/red]")


@cli.command()
@click.option("--all", "show_all", is_flag=True, help="Show all orders (including filled/canceled)")
@click.pass_context
def orders(ctx: click.Context, show_all: bool) -> None:
    """Show open orders."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        orders_list = broker.get_orders()

        if not show_all:
            # Filter to only open/pending orders
            open_statuses = {OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}
            orders_list = [o for o in orders_list if o.status in open_statuses]

        if not orders_list:
            console.print("[yellow]No open orders[/yellow]")
            return

        table = Table(title="Orders" if show_all else "Open Orders")
        table.add_column("ID", style="dim", max_width=8)
        table.add_column("Symbol", style="cyan")
        table.add_column("Side", justify="center")
        table.add_column("Type", justify="center")
        table.add_column("Qty", justify="right")
        table.add_column("Filled", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Status", justify="center")

        for order in orders_list:
            side_style = "green" if order.side == OrderSide.BUY else "red"
            side_text = f"[{side_style}]{order.side.value.upper()}[/{side_style}]"

            # Format price based on order type
            if order.order_type == OrderType.MARKET:
                price_text = "MARKET"
            elif order.order_type == OrderType.LIMIT and order.limit_price:
                price_text = f"${order.limit_price:,.2f}"
            elif order.order_type == OrderType.STOP and order.stop_price:
                price_text = f"${order.stop_price:,.2f}"
            elif order.order_type == OrderType.TRAILING_STOP and order.trail_percent:
                price_text = f"{order.trail_percent}%"
            else:
                price_text = "-"

            # Status styling
            status_styles = {
                OrderStatus.FILLED: "green",
                OrderStatus.CANCELED: "dim",
                OrderStatus.REJECTED: "red",
                OrderStatus.PARTIALLY_FILLED: "yellow",
            }
            status_style = status_styles.get(order.status, "white")
            status_text = f"[{status_style}]{order.status.value.upper()}[/{status_style}]"

            table.add_row(
                order.id[:8],
                order.symbol,
                side_text,
                order.order_type.value.upper(),
                str(order.qty),
                str(order.filled_qty),
                price_text,
                status_text,
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching orders: {e}[/red]")


@cli.command()
@click.pass_context
def portfolio(ctx: click.Context) -> None:
    """Show full portfolio overview (balance + positions + orders)."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        account = broker.get_account()
        positions_list = broker.get_positions()
        orders_list = broker.get_orders()
        market_open = broker.is_market_open()

        # Filter to open orders
        open_statuses = {OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}
        open_orders = [o for o in orders_list if o.status in open_statuses]

        # === Account Summary ===
        console.print()
        market_status = "[green]● OPEN[/green]" if market_open else "[yellow]● CLOSED[/yellow]"
        console.print(f"[bold]Account Overview[/bold]  {market_status}")
        console.print()

        # Main metrics in a compact format
        console.print(f"  Portfolio Value:  [bold]${account.portfolio_value:,.2f}[/bold]")
        console.print(f"  Cash:             ${account.cash:,.2f}")
        console.print(f"  Buying Power:     ${account.buying_power:,.2f}")

        # Day's change
        if account.last_equity:
            day_change = account.equity - account.last_equity
            day_change_pct = (day_change / account.last_equity) * 100 if account.last_equity else 0
            change_style = "green" if day_change >= 0 else "red"
            sign = "+" if day_change >= 0 else ""
            console.print(f"  Day's Change:     [{change_style}]{sign}${day_change:,.2f} ({sign}{day_change_pct:.2f}%)[/{change_style}]")

        console.print()

        # === Positions ===
        if positions_list:
            console.print(f"[bold]Positions ({len(positions_list)})[/bold]")
            console.print()

            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
            table.add_column("Symbol", style="cyan")
            table.add_column("Qty", justify="right")
            table.add_column("Price", justify="right")
            table.add_column("Value", justify="right")
            table.add_column("P/L", justify="right")
            table.add_column("%", justify="right")

            total_value = sum(p.market_value for p in positions_list)
            total_pl = sum(p.unrealized_pl for p in positions_list)

            for pos in positions_list:
                pl_style = "green" if pos.unrealized_pl >= 0 else "red"
                sign = "+" if pos.unrealized_pl >= 0 else ""
                table.add_row(
                    pos.symbol,
                    str(int(pos.qty)),
                    f"${pos.current_price:,.2f}",
                    f"${pos.market_value:,.2f}",
                    f"[{pl_style}]{sign}${pos.unrealized_pl:,.2f}[/{pl_style}]",
                    f"[{pl_style}]{sign}{pos.unrealized_pl_pct * 100:.1f}%[/{pl_style}]",
                )

            console.print(table)
            console.print()

            # Totals
            pl_style = "green" if total_pl >= 0 else "red"
            sign = "+" if total_pl >= 0 else ""
            console.print(f"  Total Value: ${total_value:,.2f}  |  Unrealized P/L: [{pl_style}]{sign}${total_pl:,.2f}[/{pl_style}]")
            console.print()
        else:
            console.print("[dim]No open positions[/dim]")
            console.print()

        # === Open Orders ===
        if open_orders:
            console.print(f"[bold]Open Orders ({len(open_orders)})[/bold]")
            console.print()

            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
            table.add_column("Symbol", style="cyan")
            table.add_column("Side")
            table.add_column("Type")
            table.add_column("Qty", justify="right")
            table.add_column("Price", justify="right")
            table.add_column("Status")

            for order in open_orders:
                side_style = "green" if order.side == OrderSide.BUY else "red"
                side_text = f"[{side_style}]{order.side.value.upper()}[/{side_style}]"

                if order.order_type == OrderType.MARKET:
                    price_text = "MKT"
                elif order.limit_price:
                    price_text = f"${order.limit_price:,.2f}"
                elif order.stop_price:
                    price_text = f"${order.stop_price:,.2f}"
                else:
                    price_text = "-"

                table.add_row(
                    order.symbol,
                    side_text,
                    order.order_type.value.upper(),
                    str(int(order.qty)),
                    price_text,
                    order.status.value.upper(),
                )

            console.print(table)
            console.print()
        else:
            console.print("[dim]No open orders[/dim]")
            console.print()

    except Exception as e:
        console.print(f"[red]Error fetching portfolio: {e}[/red]")


@cli.command()
@click.argument("symbol")
@click.pass_context
def quote(ctx: click.Context, symbol: str) -> None:
    """Get current quote for a symbol."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        q = broker.get_quote(symbol.upper())

        table = Table(title=f"Quote: {symbol.upper()}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Bid", f"${q.bid:,.2f}")
        table.add_row("Ask", f"${q.ask:,.2f}")
        table.add_row("Spread", f"${q.ask - q.bid:,.2f}")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching quote: {e}[/red]")


@cli.command()
@click.argument("symbol")
@click.argument("price", type=float)
@click.option("--qty", type=int, default=1, help="Number of shares (default: 1)")
@click.pass_context
def buy(ctx: click.Context, symbol: str, price: float, qty: int) -> None:
    """Place a limit buy order.

    Example: trader buy TSLA 399.00 --qty 1
    """
    config = ctx.obj["config"]
    logger = get_logger("autotrader.trades")

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        symbol = symbol.upper()

        order_type = OrderType.LIMIT
        limit_price = Decimal(str(price))
        console.print(f"[yellow]Placing LIMIT BUY: {qty} {symbol} @ ${price:.2f}[/yellow]")

        # Safety checks
        ledger = TradeLedger()
        checker = SafetyCheck(broker, ledger)

        check_price = Decimal(str(price))

        allowed, reason = checker.check_order(symbol, int(qty), check_price, is_buy=True)
        if not allowed:
            console.print(f"[red]Order blocked by safety checks: {reason}[/red]")
            return

        order = broker.place_order(
            symbol=symbol,
            qty=Decimal(str(qty)),
            side=OrderSide.BUY,
            order_type=order_type,
            limit_price=limit_price,
        )

        try:
            save_order(order)
        except Exception:
            # Don't block the CLI if persistence fails; log and continue
            ctx.obj["logger"].exception("Failed to persist order")

        logger.info(f"BUY {qty} {symbol} | Order ID: {order.id} | Status: {order.status.value}")

        table = Table(title="Order Placed")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Order ID", order.id)
        table.add_row("Symbol", order.symbol)
        table.add_row("Side", "BUY")
        table.add_row("Quantity", str(order.qty))
        table.add_row("Type", order.order_type.value.upper())
        if order.limit_price:
            table.add_row("Limit Price", f"${order.limit_price:,.2f}")
        table.add_row("Status", order.status.value.upper())

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error placing order: {e}[/red]")


@cli.command()
@click.argument("symbol")
@click.argument("price", type=float)
@click.option("--qty", type=int, default=1, help="Number of shares (default: 1)")
@click.pass_context
def sell(ctx: click.Context, symbol: str, price: float, qty: int) -> None:
    """Place a limit sell order.

    Example: trader sell TSLA 420.00 --qty 1
    """
    config = ctx.obj["config"]
    logger = get_logger("autotrader.trades")

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        symbol = symbol.upper()

        order_type = OrderType.LIMIT
        limit_price = Decimal(str(price))
        console.print(f"[yellow]Placing LIMIT SELL: {qty} {symbol} @ ${price:.2f}[/yellow]")

        # Safety checks
        ledger = TradeLedger()
        checker = SafetyCheck(broker, ledger)

        check_price = Decimal(str(price))

        allowed, reason = checker.check_order(symbol, int(qty), check_price, is_buy=False)
        if not allowed:
            console.print(f"[red]Order blocked by safety checks: {reason}[/red]")
            return

        order = broker.place_order(
            symbol=symbol,
            qty=Decimal(str(qty)),
            side=OrderSide.SELL,
            order_type=order_type,
            limit_price=limit_price,
        )

        try:
            save_order(order)
        except Exception:
            ctx.obj["logger"].exception("Failed to persist order")

        logger.info(f"SELL {qty} {symbol} | Order ID: {order.id} | Status: {order.status.value}")

        table = Table(title="Order Placed")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Order ID", order.id)
        table.add_row("Symbol", order.symbol)
        table.add_row("Side", "SELL")
        table.add_row("Quantity", str(order.qty))
        table.add_row("Type", order.order_type.value.upper())
        if order.limit_price:
            table.add_row("Limit Price", f"${order.limit_price:,.2f}")
        table.add_row("Status", order.status.value.upper())

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error placing order: {e}[/red]")


@cli.command()
@click.pass_context
def orders(ctx: click.Context) -> None:
    """Show open orders."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        orders_list = broker.get_orders()

        if not orders_list:
            console.print("[yellow]No open orders[/yellow]")
            return

        table = Table(title="Open Orders")
        table.add_column("ID", style="dim")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side")
        table.add_column("Type")
        table.add_column("Qty", justify="right")
        table.add_column("Limit", justify="right")
        table.add_column("Status")

        for order in orders_list:
            side_style = "green" if order.side == OrderSide.BUY else "red"
            table.add_row(
                order.id[:8] + "...",
                order.symbol,
                f"[{side_style}]{order.side.value.upper()}[/{side_style}]",
                order.order_type.value.upper(),
                str(order.qty),
                f"${order.limit_price:,.2f}" if order.limit_price else "-",
                order.status.value.upper(),
            )

        console.print(table)

        # Also show locally persisted pending orders and reserved buying power
        try:
            persisted = load_orders()
        except Exception:
            persisted = []

        if persisted:
            p_table = Table(title="Pending Orders (local)")
            p_table.add_column("ID", style="dim")
            p_table.add_column("Symbol", style="cyan")
            p_table.add_column("Side")
            p_table.add_column("Qty", justify="right")
            p_table.add_column("Limit", justify="right")
            p_table.add_column("Status")

            reserved_buy_value = Decimal("0")
            for po in persisted:
                limit_str = f"${po.limit_price:,.2f}" if po.limit_price else "-"
                p_table.add_row(po.id or "-", po.symbol, po.side.value.upper(), str(po.qty), limit_str, po.status.value.upper())

                # consider pending buys as reserved value
                if po.side.value == "buy" and po.status.value in ("new", "submitted"):
                    if po.limit_price is not None:
                        reserved_buy_value += po.limit_price * po.qty
                    else:
                        try:
                            q = broker.get_quote(po.symbol)
                            mid = (q.bid + q.ask) / 2
                        except Exception:
                            mid = Decimal("0")
                        reserved_buy_value += mid * po.qty

            console.print(p_table)
            console.print(f"\nReserved Buying Power (pending buys): [yellow]${reserved_buy_value:,.2f}[/yellow]\n")
    except Exception as e:
        console.print(f"[red]Error fetching orders: {e}[/red]")


@cli.command(name="reconcile-orders")
@click.option("--orders-dir", type=click.Path(), help="Path to config directory containing orders.yaml")
@click.pass_context
def reconcile_orders(ctx: click.Context, orders_dir: str | None) -> None:
    """Reconcile locally persisted orders with broker state."""
    config = ctx.obj["config"]

    broker = get_broker(config)

    orders_path = Path(orders_dir) if orders_dir else None
    engine = TradingEngine(broker, orders_dir=orders_path)

    console.print("Running reconciliation...")
    try:
        engine._reconcile_orders()
        console.print("[green]Reconciliation completed.[/green]")
    except Exception as e:
        console.print(f"[red]Reconciliation failed: {e}[/red]")
    


@cli.command()
@click.argument("order_id")
@click.pass_context
def cancel(ctx: click.Context, order_id: str) -> None:
    """Cancel an open order."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        success = broker.cancel_order(order_id)

        if success:
            console.print(f"[green]Order {order_id} canceled[/green]")
        else:
            console.print(f"[red]Failed to cancel order {order_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error canceling order: {e}[/red]")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Evaluate strategies but don't execute trades")
@click.option("--interval", type=int, default=60, help="Poll interval in seconds")
@click.option("--once", is_flag=True, help="Run once and exit")
@click.option("--force", is_flag=True, help="Force start even if another engine might be running")
@click.pass_context
def start(ctx: click.Context, dry_run: bool, interval: int, once: bool, force: bool) -> None:
    """Start the trading engine.

    The engine will continuously monitor prices and execute trades
    based on your configured strategies.

    Only one engine can run at a time to prevent duplicate orders.

    Examples:

        Run in paper mode:
        trader start

        Dry run (no actual trades):
        trader start --dry-run

        Run once and exit:
        trader start --once

        Custom poll interval:
        trader start --interval 30

        Force start (use with caution):
        trader start --force

        Production mode:
        trader --prod start
    """
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        env_var = "ALPACA_PROD_API_KEY" if config.is_prod else "ALPACA_API_KEY"
        console.print(f"[red]Error: {env_var} not configured[/red]")
        return

    # Interactive confirmation for production
    if config.is_prod:
        console.print("[red bold]⚠️  PRODUCTION MODE ⚠️[/red bold]")
        console.print(f"[red]You are about to trade with REAL MONEY on {config.service.value}[/red]")
        console.print(f"[dim]Using: {config.base_url}[/dim]")
        console.print()
        if not click.confirm("Are you sure you want to continue?", default=False):
            console.print("[yellow]Aborted.[/yellow]")
            return

    # Check for strategies
    active_strategies = load_strategies()
    active_strategies = [s for s in active_strategies if s.enabled and s.is_active()]

    if not active_strategies:
        console.print("[yellow]Warning: No active strategies configured[/yellow]")
        console.print("Add a strategy: trader strategy add trailing-stop AAPL --qty 10")
        if not once:
            return

    # Handle --force flag by removing stale lock file
    if force:
        lock_path = get_lock_file_path()
        if lock_path.exists():
            console.print("[yellow]Forcing start - removing existing lock file[/yellow]")
            try:
                lock_path.unlink()
            except Exception as e:
                console.print(f"[red]Error removing lock file: {e}[/red]")
                return

    broker = get_broker(config)
    engine = TradingEngine(
        broker,
        poll_interval=interval,
        dry_run=dry_run,
        strategy_defaults=config.strategy_defaults,
    )

    mode = "[yellow]DRY RUN[/yellow]" if dry_run else f"[green]{config.env.value.upper()}[/green]"
    console.print(f"Starting trading engine in {mode} mode...")
    console.print(f"Active strategies: {len(active_strategies)}")
    console.print(f"Poll interval: {interval}s")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    try:
        if once:
            order_ids = engine.run_once()
            if order_ids:
                console.print(f"[green]Executed {len(order_ids)} strategy actions[/green]")
            else:
                console.print("[yellow]No strategies triggered[/yellow]")
        else:
            engine.start()
    except EngineAlreadyRunningError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Use --force to override (use with caution)[/dim]")


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Force immediate shutdown (SIGKILL)")
def stop(force: bool) -> None:
    """Stop the running trading engine.

    By default, sends SIGTERM and waits for the current cycle to complete.
    Use --force/-f to immediately kill the engine.

    Examples:

        Graceful stop (waits for cycle):
        trader stop

        Force immediate shutdown:
        trader stop --force
        trader stop -f
    """
    import os
    import signal

    lock_path = get_lock_file_path()

    if not lock_path.exists():
        console.print("[yellow]No trading engine is currently running[/yellow]")
        return

    # Read PID from lock file
    try:
        with open(lock_path) as f:
            pid_str = f.read().strip()
            if not pid_str:
                console.print("[yellow]Lock file is empty - no engine running[/yellow]")
                lock_path.unlink()
                return
            pid = int(pid_str)
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[red]Error reading lock file: {e}[/red]")
        return

    # Check if process is actually running
    try:
        os.kill(pid, 0)  # Signal 0 just checks if process exists
    except ProcessLookupError:
        console.print(f"[yellow]Engine process (PID {pid}) is not running[/yellow]")
        console.print("[dim]Cleaning up stale lock file...[/dim]")
        try:
            lock_path.unlink()
        except Exception:
            pass
        return
    except PermissionError:
        console.print(f"[red]Permission denied to signal process {pid}[/red]")
        return

    # Send graceful shutdown signal
    sig = signal.SIGKILL if force else signal.SIGTERM
    sig_name = "SIGKILL" if force else "SIGTERM"

    try:
        os.kill(pid, sig)
        if force:
            console.print(f"[yellow]Force killed trading engine (PID {pid})[/yellow]")
            # Clean up lock file since SIGKILL won't let the process clean up
            try:
                lock_path.unlink()
            except Exception:
                pass
        else:
            console.print(f"[green]Sent shutdown signal to trading engine (PID {pid})[/green]")
            console.print("[dim]Engine will stop after current cycle completes[/dim]")
    except ProcessLookupError:
        console.print(f"[yellow]Engine already stopped[/yellow]")
    except PermissionError:
        console.print(f"[red]Permission denied to stop process {pid}[/red]")
    except Exception as e:
        console.print(f"[red]Error stopping engine: {e}[/red]")


@cli.command()
@click.pass_context
def watch(ctx: click.Context) -> None:
    """Watch prices for symbols in your strategies."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    strategies = load_strategies()
    if not strategies:
        console.print("[yellow]No strategies configured[/yellow]")
        return

    broker = get_broker(config)

    # Get unique symbols from strategies
    symbols = list(set(s.symbol for s in strategies))

    table = Table(title="Price Watch")
    table.add_column("Symbol", style="cyan")
    table.add_column("Bid", justify="right")
    table.add_column("Ask", justify="right")
    table.add_column("Strategies")

    for symbol in symbols:
        try:
            q = broker.get_quote(symbol)

            # Find strategies for this symbol
            symbol_strategies = [s for s in strategies if s.symbol == symbol]
            strat_strs = []
            for s in symbol_strategies:
                phase = s.phase.value.replace("_", " ")
                strat_strs.append(f"{s.strategy_type.value}: {phase}")

            table.add_row(
                symbol,
                f"${q.bid:,.2f}",
                f"${q.ask:,.2f}",
                ", ".join(strat_strs) if strat_strs else "-",
            )
        except Exception as e:
            table.add_row(symbol, "[red]Error[/red]", str(e), "-")

    console.print(table)


@cli.command()
@click.pass_context
def portfolio(ctx: click.Context) -> None:
    """Show portfolio summary and performance."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        ledger = TradeLedger()
        pf = Portfolio(broker, ledger)

        summary = pf.get_summary()

        # Summary table
        table = Table(title="Portfolio Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Equity", f"${summary.total_equity:,.2f}")
        table.add_row("Cash", f"${summary.cash:,.2f}")
        table.add_row("Positions Value", f"${summary.positions_value:,.2f}")
        table.add_row("Position Count", str(summary.position_count))

        # P/L styling
        unreal_style = "green" if summary.unrealized_pnl >= 0 else "red"
        real_style = "green" if summary.realized_pnl_today >= 0 else "red"
        total_style = "green" if summary.total_pnl_today >= 0 else "red"

        table.add_row(
            "Unrealized P/L",
            f"[{unreal_style}]${summary.unrealized_pnl:,.2f} ({summary.unrealized_pnl_pct:.2%})[/{unreal_style}]",
        )
        table.add_row(
            "Realized P/L (Today)",
            f"[{real_style}]${summary.realized_pnl_today:,.2f}[/{real_style}]",
        )
        table.add_row(
            "Total P/L (Today)",
            f"[{total_style}]${summary.total_pnl_today:,.2f}[/{total_style}]",
        )

        console.print(table)

        # Positions breakdown
        positions = pf.get_positions_detail()
        if positions:
            console.print()
            pos_table = Table(title="Position Breakdown")
            pos_table.add_column("Symbol", style="cyan")
            pos_table.add_column("Qty", justify="right")
            pos_table.add_column("Avg Cost", justify="right")
            pos_table.add_column("Current", justify="right")
            pos_table.add_column("Value", justify="right")
            pos_table.add_column("P/L", justify="right")
            pos_table.add_column("Weight", justify="right")

            for pos in positions:
                pl_style = "green" if pos.unrealized_pnl >= 0 else "red"
                pos_table.add_row(
                    pos.symbol,
                    str(pos.quantity),
                    f"${pos.avg_cost:,.2f}",
                    f"${pos.current_price:,.2f}",
                    f"${pos.market_value:,.2f}",
                    f"[{pl_style}]${pos.unrealized_pnl:,.2f}[/{pl_style}]",
                    f"{pos.weight_pct:.1f}%",
                )

            console.print(pos_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option("--symbol", help="Filter by symbol")
@click.option("--limit", type=int, default=20, help="Number of trades to show")
@click.pass_context
def history(ctx: click.Context, symbol: str | None, limit: int) -> None:
    """Show trade history."""
    ledger = TradeLedger()
    trades = ledger.get_trades(symbol=symbol, limit=limit)

    if not trades:
        console.print("[yellow]No trades recorded[/yellow]")
        return

    table = Table(title=f"Trade History{f' - {symbol}' if symbol else ''}")
    table.add_column("Time", style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Side")
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Status")

    for trade in trades:
        side_style = "green" if trade.is_buy else "red"
        time_str = trade.timestamp.strftime("%m/%d %H:%M")
        table.add_row(
            time_str,
            trade.symbol,
            f"[{side_style}]{trade.side.upper()}[/{side_style}]",
            str(trade.quantity),
            f"${trade.price:,.2f}",
            f"${trade.total:,.2f}",
            trade.status.upper(),
        )

    console.print(table)

    # Show today's P/L
    today_pnl = ledger.get_total_today_pnl()
    pnl_style = "green" if today_pnl >= 0 else "red"
    console.print(f"\nToday's Realized P/L: [{pnl_style}]${today_pnl:,.2f}[/{pnl_style}]")


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--days", type=int, default=30, help="Export trades from last N days")
@click.pass_context
def export(ctx: click.Context, output: str, days: int) -> None:
    """Export trade history to CSV."""
    from datetime import timedelta

    ledger = TradeLedger()
    since = datetime.now() - timedelta(days=days)
    path = Path(output)

    count = ledger.export_csv(path, since=since)
    console.print(f"[green]Exported {count} trades to {path}[/green]")


@cli.command()
@click.pass_context
def safety(ctx: click.Context) -> None:
    """Show safety controls status."""
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    try:
        broker = get_broker(config)
        ledger = TradeLedger()
        checker = SafetyCheck(broker, ledger)

        status = checker.get_status()

        table = Table(title="Safety Controls")
        table.add_column("Control", style="cyan")
        table.add_column("Status", justify="right")
        table.add_column("Limit", justify="right")

        # Kill switch
        kill_status = "[red]ACTIVE[/red]" if status["kill_switch"] else "[green]OFF[/green]"
        table.add_row("Kill Switch", kill_status, "-")

        # Daily P/L
        pnl = status["daily_pnl"]
        pnl_style = "green" if pnl >= 0 else "red"
        remaining = status["daily_pnl_remaining"]
        table.add_row(
            "Daily P/L",
            f"[{pnl_style}]${pnl:,.2f}[/{pnl_style}]",
            f"${status['daily_pnl_limit']:,.2f}",
        )
        table.add_row("Loss Remaining", f"${remaining:,.2f}", "-")

        # Trade count
        trades = status["trade_count"]
        limit = status["trade_limit"]
        pct = trades / limit * 100 if limit > 0 else 0
        table.add_row("Trades Today", f"{trades} ({pct:.0f}%)", str(limit))
        table.add_row("Trades Remaining", str(status["trades_remaining"]), "-")

        # Can trade
        can_trade = status["can_trade"]
        trade_status = "[green]YES[/green]" if can_trade else "[red]NO[/red]"
        table.add_row("Can Trade", trade_status, "-")

        console.print(table)

        # Show limits
        console.print()
        limits = SafetyLimits()
        limit_table = Table(title="Position Limits")
        limit_table.add_column("Limit", style="cyan")
        limit_table.add_column("Value", justify="right")

        limit_table.add_row("Max Position Size", f"{limits.max_position_size} shares")
        limit_table.add_row("Max Position Value", f"${limits.max_position_value:,.2f}")
        limit_table.add_row("Max Order Value", f"${limits.max_order_value:,.2f}")
        limit_table.add_row("Max Daily Loss", f"${limits.max_daily_loss:,.2f}")
        limit_table.add_row("Max Daily Trades", str(limits.max_daily_trades))

        console.print(limit_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def kill(ctx: click.Context) -> None:
    """Activate kill switch - stops all automated trading."""
    console.print("[red]KILL SWITCH ACTIVATED[/red]")
    console.print("All automated trading is now stopped.")
    console.print("Manual trades via buy/sell commands are still allowed.")
    console.print("\nTo reset, restart the trading engine.")


@cli.command()
@click.argument("symbols", nargs=-1)
@click.pass_context
def scan(ctx: click.Context, symbols: tuple[str, ...]) -> None:
    """Scan symbols for current prices.

    Examples:

        Scan specific symbols:
        trader scan AAPL TSLA GOOGL

        Scan all symbols in strategies:
        trader scan
    """
    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        console.print("[red]Error: Alpaca API key not configured[/red]")
        return

    # Get symbols from strategies if none provided
    if not symbols:
        strategies = load_strategies()
        symbols = tuple(set(s.symbol for s in strategies))

    if not symbols:
        console.print("[yellow]No symbols to scan[/yellow]")
        console.print("Provide symbols: trader scan AAPL TSLA")
        return

    broker = get_broker(config)
    strategies = load_strategies()

    table = Table(title="Market Scan")
    table.add_column("Symbol", style="cyan")
    table.add_column("Bid", justify="right")
    table.add_column("Ask", justify="right")
    table.add_column("Spread", justify="right")
    table.add_column("Strategies")

    for symbol in symbols:
        symbol = symbol.upper()
        try:
            q = broker.get_quote(symbol)
            mid = (q.bid + q.ask) / 2
            spread = q.ask - q.bid
            spread_pct = (spread / mid * 100) if mid > 0 else Decimal("0")

            # Find strategies for this symbol
            symbol_strategies = [s for s in strategies if s.symbol == symbol]

            strat_strs = []
            for s in symbol_strategies:
                strat_strs.append(f"{s.strategy_type.value}: {s.phase.value}")

            table.add_row(
                symbol,
                f"${q.bid:,.2f}",
                f"${q.ask:,.2f}",
                f"${spread:.2f} ({spread_pct:.2f}%)",
                ", ".join(strat_strs) if strat_strs else "-",
            )

        except Exception as e:
            table.add_row(symbol, "[red]Error[/red]", "-", "-", str(e))

    console.print(table)


# =============================================================================
# Strategy Commands
# =============================================================================

from trader.strategies.models import Strategy, StrategyType, StrategyPhase, EntryType
from trader.strategies.loader import (
    load_strategies,
    save_strategy,
    delete_strategy,
    get_strategy,
    enable_strategy,
)


STRATEGY_HELP = {
    "trailing-stop": """
TRAILING STOP STRATEGY

Rides the trend and locks in gains. When price rises, the stop follows.
When price drops by the trailing percentage, it sells to protect profits.

Best for: Trending stocks you want to hold but protect gains

Example:
    trader strategy add trailing-stop AAPL --qty 10 --trailing-pct 5

    This buys 10 AAPL at market price. As price rises, a trailing stop
    follows 5% behind. If price drops 5% from any high, sells to lock profit.
""",
    "bracket": """
BRACKET STRATEGY

Defined risk/reward with both take-profit and stop-loss. Whichever hits
first closes the position. Classic risk management approach.

Best for: Trades where you know your target and max acceptable loss

Example:
    trader strategy add bracket TSLA --qty 5 --take-profit 10 --stop-loss 5

    Buys 5 TSLA. Sets take-profit at +10% and stop-loss at -5%.
    First one hit closes the position.
""",
    "scale-out": """
SCALE OUT STRATEGY

Captures gains progressively while letting winners run. Sells portions
of your position at different profit targets.

Best for: Strong conviction plays where you want to lock some gains

Example:
    trader strategy add scale-out GOOGL --qty 30

    Buys 30 shares. Default targets: sell 33% at +5%, 33% at +10%, 34% at +15%.
""",
    "grid": """
GRID STRATEGY

Profits from sideways volatility by buying at regular intervals on the
way down and selling on the way up. Works best in ranging markets.

Best for: Stocks that trade in a predictable range

Example:
    trader strategy add grid NVDA --qty 50 --levels 5

    Creates a grid with 5 buy levels below current price and
    5 sell levels above. Profits from price oscillation.
""",
}


@cli.group()
def strategy() -> None:
    """Manage trading strategies.

    Strategies are automated trading plans that handle both entry and exit.
    Unlike simple rules that fire once, strategies manage the complete trade
    lifecycle.

    Available strategies:
    - trailing-stop: Ride trends, lock in gains with trailing stop
    - bracket: Defined risk/reward with take-profit and stop-loss
    - scale-out: Sell portions at progressive profit targets
    - grid: Profit from sideways volatility

    Run 'trader strategy add --help' for more details.
    """
    pass


@strategy.command("list")
@click.pass_context
def strategy_list(ctx: click.Context) -> None:
    """List all trading strategies."""
    strategies = load_strategies()

    if not strategies:
        console.print("[yellow]No strategies configured[/yellow]")
        console.print("\nAdd a strategy with:")
        console.print("  trader strategy add trailing-stop AAPL --qty 10")
        console.print("\nSee available strategies:")
        console.print("  trader strategy add --help")
        return

    table = Table(title="Trading Strategies")
    table.add_column("ID", style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Type")
    table.add_column("Qty", justify="right")
    table.add_column("Phase")
    table.add_column("Details")

    for s in strategies:
        # Phase styling
        phase_styles = {
            StrategyPhase.PENDING: "[yellow]PENDING[/yellow]",
            StrategyPhase.ENTRY_ACTIVE: "[blue]ENTERING[/blue]",
            StrategyPhase.POSITION_OPEN: "[green]OPEN[/green]",
            StrategyPhase.EXITING: "[blue]EXITING[/blue]",
            StrategyPhase.COMPLETED: "[dim]DONE[/dim]",
            StrategyPhase.FAILED: "[red]FAILED[/red]",
            StrategyPhase.PAUSED: "[yellow]PAUSED[/yellow]",
        }
        phase_str = phase_styles.get(s.phase, s.phase.value)

        if not s.enabled:
            phase_str = "[dim]DISABLED[/dim]"

        # Build details string based on strategy type
        details = []
        if s.strategy_type == StrategyType.TRAILING_STOP:
            details.append(f"trail: {s.trailing_stop_pct}%")
            if s.high_watermark:
                details.append(f"high: ${s.high_watermark:.2f}")
        elif s.strategy_type == StrategyType.BRACKET:
            details.append(f"TP: +{s.take_profit_pct}%")
            details.append(f"SL: -{s.stop_loss_pct}%")
        elif s.strategy_type == StrategyType.SCALE_OUT:
            if s.scale_targets:
                targets = [f"+{t['target_pct']}%" for t in s.scale_targets]
                details.append(f"targets: {', '.join(targets)}")

        if s.entry_fill_price:
            details.insert(0, f"entry: ${s.entry_fill_price:.2f}")

        table.add_row(
            s.id,
            s.symbol,
            s.strategy_type.value.replace("_", "-"),
            str(s.quantity),
            phase_str,
            " | ".join(details) if details else "-",
        )

    console.print(table)


@strategy.command("add")
@click.argument("strategy_type", type=click.Choice(["trailing-stop", "bracket", "scale-out", "grid"]))
@click.argument("symbol")
@click.option("--qty", type=int, default=1, help="Number of shares (default: 1)")
@click.option("--trailing-pct", type=float, help="Trailing stop percentage (for trailing-stop)")
@click.option("--take-profit", type=float, help="Take profit percentage (for bracket)")
@click.option("--stop-loss", type=float, help="Stop loss percentage (for bracket)")
@click.option("--limit", "-L", type=float, help="Limit price for entry (default: market order)")
@click.option("--levels", type=int, help="Number of grid levels (for grid)")
@click.pass_context
def strategy_add(
    ctx: click.Context,
    strategy_type: str,
    symbol: str,
    qty: int,
    trailing_pct: Optional[float],
    take_profit: Optional[float],
    stop_loss: Optional[float],
    limit: Optional[float],
    levels: Optional[int],
) -> None:
    """Add a new trading strategy.

    STRATEGY TYPES:

    \b
    trailing-stop  Ride trends, lock in gains with a trailing stop
    bracket        Take-profit AND stop-loss (OCO style)
    scale-out      Sell portions at progressive profit targets
    grid           Buy low intervals, sell high intervals

    \b
    EXAMPLES:
        trader strategy add trailing-stop AAPL --qty 10 --trailing-pct 5
        trader strategy add bracket TSLA --qty 5 --take-profit 10 --stop-loss 5
        trader strategy add scale-out GOOGL --qty 20
        trader strategy add grid NVDA --levels 5

    Use --limit/-L to enter at a specific price instead of market.
    """
    config = ctx.obj["config"]
    defaults = config.strategy_defaults

    # Normalize strategy type
    strat_type_map = {
        "trailing-stop": StrategyType.TRAILING_STOP,
        "bracket": StrategyType.BRACKET,
        "scale-out": StrategyType.SCALE_OUT,
        "grid": StrategyType.GRID,
    }
    strat_type = strat_type_map[strategy_type]

    # Determine entry type based on --limit flag
    entry_type = EntryType.LIMIT if limit else EntryType.MARKET
    entry_price = Decimal(str(limit)) if limit else None

    # Build strategy based on type
    try:
        if strat_type == StrategyType.TRAILING_STOP:
            trailing = Decimal(str(trailing_pct)) if trailing_pct else defaults.trailing_stop_pct
            strat = Strategy(
                symbol=symbol.upper(),
                strategy_type=strat_type,
                quantity=qty,
                entry_type=entry_type,
                entry_price=entry_price,
                trailing_stop_pct=trailing,
            )
            detail_str = f"trailing stop: {trailing}%"

        elif strat_type == StrategyType.BRACKET:
            tp = Decimal(str(take_profit)) if take_profit else defaults.take_profit_pct
            sl = Decimal(str(stop_loss)) if stop_loss else defaults.stop_loss_pct
            strat = Strategy(
                symbol=symbol.upper(),
                strategy_type=strat_type,
                quantity=qty,
                entry_type=entry_type,
                entry_price=entry_price,
                take_profit_pct=tp,
                stop_loss_pct=sl,
            )
            detail_str = f"take-profit: +{tp}%, stop-loss: -{sl}%"

        elif strat_type == StrategyType.SCALE_OUT:
            strat = Strategy(
                symbol=symbol.upper(),
                strategy_type=strat_type,
                quantity=qty,
                entry_type=entry_type,
                entry_price=entry_price,
                scale_targets=defaults.scale_tranches,
            )
            targets = [f"+{t['target_pct']}%" for t in defaults.scale_tranches]
            detail_str = f"targets: {', '.join(targets)}"

        elif strat_type == StrategyType.GRID:
            # For grid, we need to get current price to set range
            if not config.alpaca_api_key:
                console.print("[red]Error: Alpaca API key required for grid strategy[/red]")
                return

            broker = get_broker(config)
            quote = broker.get_quote(symbol.upper())
            mid_price = (quote.bid + quote.ask) / 2

            grid_levels = levels or defaults.grid_levels
            spacing = defaults.grid_spacing_pct

            # Calculate grid range (symmetric around current price)
            low = mid_price * (1 - (spacing * grid_levels) / 100)
            high = mid_price * (1 + (spacing * grid_levels) / 100)

            strat = Strategy(
                symbol=symbol.upper(),
                strategy_type=strat_type,
                quantity=qty,
                grid_config={
                    "low": float(low),
                    "high": float(high),
                    "levels": grid_levels,
                    "qty_per_level": defaults.grid_qty_per_level,
                },
            )
            detail_str = f"range: ${low:.2f}-${high:.2f}, {grid_levels} levels"

        else:
            console.print(f"[red]Unknown strategy type: {strategy_type}[/red]")
            return

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Save the strategy
    save_strategy(strat)

    console.print(f"[green]Strategy added:[/green] {strategy_type} {qty} {symbol.upper()}")
    console.print(f"[dim]ID: {strat.id}[/dim]")
    entry_str = f"limit @ ${limit:.2f}" if limit else "market"
    console.print(f"[dim]Entry: {entry_str}[/dim]")
    console.print(f"[dim]{detail_str}[/dim]")
    console.print()
    console.print("Start the engine to activate: [cyan]trader start[/cyan]")


@strategy.command("show")
@click.argument("strategy_id")
@click.pass_context
def strategy_show(ctx: click.Context, strategy_id: str) -> None:
    """Show details of a specific strategy."""
    strat = get_strategy(strategy_id)

    if strat is None:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")
        return

    console.print(f"\n[bold]{strat.strategy_type.value.replace('_', '-').upper()}[/bold] Strategy")
    console.print(f"ID: {strat.id}")
    console.print(f"Symbol: [cyan]{strat.symbol}[/cyan]")
    console.print(f"Quantity: {strat.quantity}")
    console.print(f"Phase: {strat.phase.value}")
    console.print(f"Enabled: {'Yes' if strat.enabled else 'No'}")
    console.print()

    console.print("[bold]Entry Configuration[/bold]")
    console.print(f"  Type: {strat.entry_type.value}")
    if strat.entry_price:
        console.print(f"  Price: ${strat.entry_price:.2f}")
    if strat.entry_order_id:
        console.print(f"  Order ID: {strat.entry_order_id}")
    if strat.entry_fill_price:
        console.print(f"  Fill Price: ${strat.entry_fill_price:.2f}")
    console.print()

    console.print("[bold]Exit Configuration[/bold]")
    if strat.strategy_type == StrategyType.TRAILING_STOP:
        console.print(f"  Trailing Stop: {strat.trailing_stop_pct}%")
        if strat.high_watermark:
            console.print(f"  High Watermark: ${strat.high_watermark:.2f}")
            stop_price = strat.high_watermark * (1 - strat.trailing_stop_pct / 100)
            console.print(f"  Current Stop: ${stop_price:.2f}")
    elif strat.strategy_type == StrategyType.BRACKET:
        console.print(f"  Take Profit: +{strat.take_profit_pct}%")
        console.print(f"  Stop Loss: -{strat.stop_loss_pct}%")
        if strat.entry_fill_price:
            tp_price = strat.entry_fill_price * (1 + strat.take_profit_pct / 100)
            sl_price = strat.entry_fill_price * (1 - strat.stop_loss_pct / 100)
            console.print(f"  TP Target: ${tp_price:.2f}")
            console.print(f"  SL Target: ${sl_price:.2f}")
    elif strat.strategy_type == StrategyType.SCALE_OUT and strat.scale_targets:
        console.print("  Targets:")
        for t in strat.scale_targets:
            console.print(f"    - {t['pct']}% at +{t['target_pct']}%")
    elif strat.strategy_type == StrategyType.GRID and strat.grid_config:
        console.print(f"  Range: ${strat.grid_config['low']:.2f} - ${strat.grid_config['high']:.2f}")
        console.print(f"  Levels: {strat.grid_config['levels']}")
        console.print(f"  Qty/Level: {strat.grid_config['qty_per_level']}")

    if strat.exit_order_ids:
        console.print(f"  Exit Orders: {', '.join(strat.exit_order_ids)}")
    console.print()

    console.print("[bold]Metadata[/bold]")
    console.print(f"  Created: {strat.created_at}")
    console.print(f"  Updated: {strat.updated_at}")
    if strat.notes:
        console.print(f"  Notes: {strat.notes}")


@strategy.command("remove")
@click.argument("strategy_id")
@click.pass_context
def strategy_remove(ctx: click.Context, strategy_id: str) -> None:
    """Remove a trading strategy."""
    if delete_strategy(strategy_id):
        console.print(f"[green]Strategy {strategy_id} removed[/green]")
    else:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")


@strategy.command("enable")
@click.argument("strategy_id")
@click.pass_context
def strategy_enable(ctx: click.Context, strategy_id: str) -> None:
    """Enable a trading strategy."""
    if enable_strategy(strategy_id, enabled=True):
        console.print(f"[green]Strategy {strategy_id} enabled[/green]")
    else:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")


@strategy.command("disable")
@click.argument("strategy_id")
@click.pass_context
def strategy_disable(ctx: click.Context, strategy_id: str) -> None:
    """Disable a trading strategy."""
    if enable_strategy(strategy_id, enabled=False):
        console.print(f"[yellow]Strategy {strategy_id} disabled[/yellow]")
    else:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")


@strategy.command("pause")
@click.argument("strategy_id")
@click.pass_context
def strategy_pause(ctx: click.Context, strategy_id: str) -> None:
    """Pause an active strategy."""
    strat = get_strategy(strategy_id)
    if strat is None:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")
        return

    if strat.is_terminal():
        console.print(f"[yellow]Strategy is already {strat.phase.value}[/yellow]")
        return

    strat.update_phase(StrategyPhase.PAUSED)
    save_strategy(strat)
    console.print(f"[yellow]Strategy {strategy_id} paused[/yellow]")


@strategy.command("resume")
@click.argument("strategy_id")
@click.pass_context
def strategy_resume(ctx: click.Context, strategy_id: str) -> None:
    """Resume a paused strategy."""
    strat = get_strategy(strategy_id)
    if strat is None:
        console.print(f"[red]Strategy {strategy_id} not found[/red]")
        return

    if strat.phase != StrategyPhase.PAUSED:
        console.print(f"[yellow]Strategy is not paused (current: {strat.phase.value})[/yellow]")
        return

    # Resume to position_open if we have a fill, otherwise pending
    if strat.entry_fill_price:
        strat.update_phase(StrategyPhase.POSITION_OPEN)
    else:
        strat.update_phase(StrategyPhase.PENDING)

    save_strategy(strat)
    console.print(f"[green]Strategy {strategy_id} resumed ({strat.phase.value})[/green]")


@strategy.command("explain")
@click.argument("strategy_type", type=click.Choice(["trailing-stop", "bracket", "scale-out", "grid"]))
def strategy_explain(strategy_type: str) -> None:
    """Explain how a strategy type works."""
    help_text = STRATEGY_HELP.get(strategy_type, "No help available")
    console.print(help_text)


# ============================================================================
# BACKTEST COMMANDS
# ============================================================================


@cli.group()
def backtest() -> None:
    """Run and analyze backtests.

    Backtesting allows you to test trading strategies against historical
    data before risking real capital. This helps validate strategy logic,
    optimize parameters, and build confidence.

    Available commands:
    - run: Run a backtest on historical data
    - list: List all saved backtests
    - show: Show detailed results for a backtest
    - compare: Compare multiple backtests side-by-side
    """
    pass


@cli.command()
@click.argument("source")
@click.option(
    "--data-source",
    type=click.Choice(["csv", "alpaca", "cached"]),
    default="csv",
    help="Data source for charting",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True),
    help="Backtests directory (containing backtests/)",
)
@click.option(
    "--historical-dir",
    type=click.Path(exists=True),
    help="Historical data directory for charting",
)
@click.option("--output", type=click.Path(dir_okay=False), help="Save chart to HTML file")
@click.option("--show", is_flag=True, help="Open chart in browser")
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
    show_default=True,
    help="Chart theme",
)
@click.pass_context
def visualize(
    ctx: click.Context,
    source: str,
    data_source: str,
    data_dir: Optional[str],
    historical_dir: Optional[str],
    output: Optional[str],
    show: bool,
    theme: str,
) -> None:
    """Visualize a backtest result from ID or JSON file."""
    if not output and not show:
        console.print("[red]Provide --output or --show to render a chart[/red]")
        return

    from trader.backtest import load_backtest
    from trader.backtest.results import BacktestResult

    result = None
    source_path = Path(source)
    if source_path.exists():
        try:
            import json

            with open(source_path, "r") as f:
                data = json.load(f)
            result = BacktestResult.from_dict(data)
        except Exception as exc:
            console.print(f"[red]Error loading backtest file: {exc}[/red]")
            return
    else:
        data_dir_path = Path(data_dir) if data_dir else None
        try:
            result = load_backtest(source, data_dir=data_dir_path)
        except FileNotFoundError:
            console.print(f"[red]Backtest {source} not found[/red]")
            return
        except Exception as exc:
            console.print(f"[red]Error loading backtest: {exc}[/red]")
            return

    _render_backtest_chart(
        result=result,
        data_source=data_source,
        historical_dir=historical_dir,
        chart_path=output,
        show=show,
        theme=theme,
    )


@cli.command()
@click.argument("strategy_type", type=click.Choice(["trailing-stop", "bracket"]))
@click.option("--symbol", required=True, help="Trading symbol")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
@click.option(
    "--params",
    multiple=True,
    required=True,
    help="Parameter grid (e.g. trailing_stop_pct:1,2,3)",
)
@click.option(
    "--objective",
    type=click.Choice(
        [
            "total_return_pct",
            "total_return",
            "win_rate",
            "profit_factor",
            "max_drawdown_pct",
        ]
    ),
    default="total_return_pct",
    show_default=True,
    help="Optimization objective",
)
@click.option(
    "--method",
    type=click.Choice(["grid", "random"]),
    default="grid",
    show_default=True,
    help="Search method",
)
@click.option("--num-samples", type=int, help="Number of samples for random search")
@click.option(
    "--data-source",
    type=click.Choice(["csv", "alpaca", "cached"]),
    default="csv",
    help="Historical data source",
)
@click.option("--data-dir", type=click.Path(exists=True), help="Historical data directory")
@click.option(
    "--results-dir",
    type=click.Path(exists=True),
    help="Directory to save optimization results",
)
@click.option("--initial-capital", type=float, default=100000.0, help="Starting capital")
@click.option("--save/--no-save", default=True, help="Save optimization results")
@click.option("--show-results", is_flag=True, help="Display results summary")
@click.pass_context
def optimize(
    ctx: click.Context,
    strategy_type: str,
    symbol: str,
    start: str,
    end: str,
    params: tuple[str, ...],
    objective: str,
    method: str,
    num_samples: Optional[int],
    data_source: str,
    data_dir: Optional[str],
    results_dir: Optional[str],
    initial_capital: float,
    save: bool,
    show_results: bool,
) -> None:
    """Optimize strategy parameters using backtests."""
    from trader.optimization import Optimizer, save_optimization

    logger = ctx.obj["logger"]

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        param_grid = _parse_param_grid(params)
        _validate_optimization_params(strategy_type, param_grid)

        optimizer = Optimizer(
            strategy_type=strategy_type,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            objective=objective,
            data_source=data_source,
            data_dir=data_dir,
            initial_capital=initial_capital,
        )

        result = optimizer.optimize(
            param_grid=param_grid,
            method=method,
            num_samples=num_samples,
        )

        if save:
            save_optimization(
                result,
                data_dir=Path(results_dir) if results_dir else None,
            )
            console.print(f"[green]Optimization saved with ID: {result.id}[/green]")

        if show_results:
            _display_optimization_result(result)

    except Exception as exc:
        logger.error(f"Optimization failed: {exc}", exc_info=True)
        console.print(f"[red]Error running optimization: {exc}[/red]")


@backtest.command("run")
@click.argument("strategy_type", type=click.Choice(["trailing-stop", "bracket"]))
@click.argument("symbol")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
@click.option("--qty", type=int, default=10, help="Quantity to trade")
@click.option("--trailing-pct", type=float, help="Trailing stop percentage (for trailing-stop)")
@click.option("--take-profit", type=float, help="Take profit percentage (for bracket)")
@click.option("--stop-loss", type=float, help="Stop loss percentage (for bracket)")
@click.option(
    "--data-source",
    type=click.Choice(["csv", "alpaca", "cached"]),
    default="csv",
    help="Data source",
)
@click.option("--data-dir", type=click.Path(exists=True), help="Directory containing CSV data files")
@click.option("--initial-capital", type=float, default=100000.0, help="Starting capital")
@click.option("--save/--no-save", default=True, help="Save backtest results")
@click.option("--chart", type=click.Path(dir_okay=False), help="Save chart to HTML file")
@click.option("--show", is_flag=True, help="Open chart in browser")
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
    show_default=True,
    help="Chart theme",
)
@click.pass_context
def backtest_run(
    ctx: click.Context,
    strategy_type: str,
    symbol: str,
    start: str,
    end: str,
    qty: int,
    trailing_pct: Optional[float],
    take_profit: Optional[float],
    stop_loss: Optional[float],
    data_source: str,
    data_dir: Optional[str],
    initial_capital: float,
    save: bool,
    chart: Optional[str],
    show: bool,
    theme: str,
) -> None:
    """Run a backtest for a strategy."""
    from trader.backtest import (
        BacktestEngine,
        HistoricalBroker,
        load_data_for_backtest,
        save_backtest,
    )
    from trader.strategies.models import StrategyType

    logger = ctx.obj["logger"]

    try:
        # Parse dates
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        # Validate parameters
        if strategy_type == "trailing-stop":
            if trailing_pct is None:
                console.print("[red]Error: --trailing-pct is required for trailing-stop strategy[/red]")
                return
            strategy_config = {
                "symbol": symbol,
                "strategy_type": "trailing_stop",
                "quantity": qty,
                "trailing_stop_pct": str(trailing_pct),
            }
        elif strategy_type == "bracket":
            if take_profit is None or stop_loss is None:
                console.print("[red]Error: --take-profit and --stop-loss are required for bracket strategy[/red]")
                return
            strategy_config = {
                "symbol": symbol,
                "strategy_type": "bracket",
                "quantity": qty,
                "take_profit_pct": str(take_profit),
                "stop_loss_pct": str(stop_loss),
            }
        else:
            console.print(f"[red]Strategy type {strategy_type} not implemented yet[/red]")
            return

        # Load historical data
        console.print(f"[cyan]Loading historical data for {symbol}...[/cyan]")

        if data_dir is None:
            data_dir_path = Path.cwd() / "data" / "historical"
        else:
            data_dir_path = Path(data_dir)

        historical_data = load_data_for_backtest(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            data_source=data_source,
            data_dir=data_dir_path,
        )

        # Create broker and engine
        broker = HistoricalBroker(
            historical_data=historical_data,
            initial_cash=Decimal(str(initial_capital)),
        )

        engine = BacktestEngine(
            broker=broker,
            strategy_config=strategy_config,
            start_date=start_date,
            end_date=end_date,
        )

        # Run backtest
        console.print(f"[cyan]Running backtest...[/cyan]")
        result = engine.run()

        # Save if requested
        if save:
            save_backtest(result)
            console.print(f"[green]Backtest saved with ID: {result.id}[/green]")

        # Display results
        _display_backtest_result(result)
        _render_backtest_chart(
            result=result,
            data_source=data_source,
            historical_dir=str(data_dir_path),
            chart_path=chart,
            show=show,
            theme=theme,
        )

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print(f"[yellow]Make sure CSV file exists at: {data_dir_path}/{symbol}.csv[/yellow]")
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        console.print(f"[red]Error running backtest: {e}[/red]")


@backtest.command("list")
@click.option("--data-dir", type=click.Path(exists=True), help="Data directory")
@click.pass_context
def backtest_list(ctx: click.Context, data_dir: Optional[str]) -> None:
    """List all saved backtests."""
    from trader.backtest import list_backtests

    data_dir_path = Path(data_dir) if data_dir else None

    try:
        backtests = list_backtests(data_dir=data_dir_path)

        if not backtests:
            console.print("[yellow]No backtests found[/yellow]")
            return

        table = Table(title="Backtest Results")
        table.add_column("ID", style="cyan")
        table.add_column("Symbol", style="white")
        table.add_column("Strategy", style="blue")
        table.add_column("Date Range", style="white")
        table.add_column("Return %", style="green")
        table.add_column("Win Rate", style="yellow")
        table.add_column("Trades", style="white")
        table.add_column("Max DD %", style="red")

        for bt in backtests:
            return_pct = Decimal(bt["total_return_pct"])
            return_color = "green" if return_pct > 0 else "red"
            return_str = f"[{return_color}]{return_pct:+.2f}%[/{return_color}]"

            win_rate = Decimal(bt["win_rate"])
            date_range = f"{bt['start_date'][:10]} to {bt['end_date'][:10]}"

            table.add_row(
                bt["id"],
                bt["symbol"],
                bt["strategy_type"],
                date_range,
                return_str,
                f"{win_rate:.1f}%",
                str(bt["total_trades"]),
                f"{Decimal(bt['max_drawdown_pct']):.2f}%",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing backtests: {e}[/red]")


@backtest.command("show")
@click.argument("backtest_id")
@click.option("--data-dir", type=click.Path(exists=True), help="Data directory")
@click.option(
    "--historical-dir",
    type=click.Path(exists=True),
    help="Historical data directory for charting",
)
@click.option(
    "--data-source",
    type=click.Choice(["csv", "alpaca", "cached"]),
    default="csv",
    help="Data source for charting",
)
@click.option("--chart", type=click.Path(dir_okay=False), help="Save chart to HTML file")
@click.option("--show", is_flag=True, help="Open chart in browser")
@click.option(
    "--theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
    show_default=True,
    help="Chart theme",
)
@click.pass_context
def backtest_show(
    ctx: click.Context,
    backtest_id: str,
    data_dir: Optional[str],
    historical_dir: Optional[str],
    data_source: str,
    chart: Optional[str],
    show: bool,
    theme: str,
) -> None:
    """Show detailed results for a backtest."""
    from trader.backtest import load_backtest

    data_dir_path = Path(data_dir) if data_dir else None

    try:
        result = load_backtest(backtest_id, data_dir=data_dir_path)
        _display_backtest_result(result, detailed=True)
        _render_backtest_chart(
            result=result,
            data_source=data_source,
            historical_dir=historical_dir,
            chart_path=chart,
            show=show,
            theme=theme,
        )

    except FileNotFoundError:
        console.print(f"[red]Backtest {backtest_id} not found[/red]")
    except Exception as e:
        console.print(f"[red]Error loading backtest: {e}[/red]")


@backtest.command("compare")
@click.argument("backtest_ids", nargs=-1, required=True)
@click.option("--data-dir", type=click.Path(exists=True), help="Data directory")
@click.pass_context
def backtest_compare(ctx: click.Context, backtest_ids: tuple[str, ...], data_dir: Optional[str]) -> None:
    """Compare multiple backtests side-by-side."""
    from trader.backtest import load_backtest

    data_dir_path = Path(data_dir) if data_dir else None

    try:
        results = []
        for bt_id in backtest_ids:
            try:
                result = load_backtest(bt_id, data_dir=data_dir_path)
                results.append(result)
            except FileNotFoundError:
                console.print(f"[yellow]Warning: Backtest {bt_id} not found, skipping[/yellow]")

        if not results:
            console.print("[red]No backtests found to compare[/red]")
            return

        # Comparison table
        table = Table(title="Backtest Comparison")
        table.add_column("Metric", style="cyan")
        for result in results:
            table.add_column(f"{result.id[:6]}...", style="white")

        # Add rows for key metrics
        metrics = [
            ("Symbol", lambda r: r.symbol),
            ("Strategy", lambda r: r.strategy_type),
            ("Date Range", lambda r: f"{r.start_date.date()} to {r.end_date.date()}"),
            ("Initial Capital", lambda r: f"${r.initial_capital:,.2f}"),
            ("Final Equity", lambda r: f"${r.initial_capital + r.total_return:,.2f}"),
            ("Total Return", lambda r: f"${r.total_return:+,.2f}"),
            ("Return %", lambda r: f"{r.total_return_pct:+.2f}%"),
            ("Total Trades", lambda r: str(r.total_trades)),
            ("Win Rate", lambda r: f"{r.win_rate:.1f}%"),
            ("Profit Factor", lambda r: f"{r.profit_factor:.2f}"),
            ("Max Drawdown", lambda r: f"${r.max_drawdown:,.2f}"),
            ("Max Drawdown %", lambda r: f"{r.max_drawdown_pct:.2f}%"),
            ("Avg Win", lambda r: f"${r.avg_win:,.2f}"),
            ("Avg Loss", lambda r: f"${r.avg_loss:,.2f}"),
        ]

        for metric_name, metric_fn in metrics:
            row = [metric_name]
            for result in results:
                row.append(metric_fn(result))
            table.add_row(*row)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error comparing backtests: {e}[/red]")


def _display_backtest_result(result, detailed: bool = False) -> None:
    """Display backtest result in a formatted table."""
    # Summary table
    table = Table(title=f"Backtest Results - {result.id}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    # Basic info
    table.add_row("Symbol", result.symbol)
    table.add_row("Strategy", result.strategy_type)
    table.add_row("Date Range", f"{result.start_date.date()} to {result.end_date.date()}")

    # Performance
    return_color = "green" if result.total_return > 0 else "red"
    table.add_row("Initial Capital", f"${result.initial_capital:,.2f}")
    table.add_row("Final Equity", f"${result.initial_capital + result.total_return:,.2f}")
    table.add_row("Total Return", f"[{return_color}]${result.total_return:+,.2f}[/{return_color}]")
    table.add_row("Return %", f"[{return_color}]{result.total_return_pct:+.2f}%[/{return_color}]")

    # Trade stats
    table.add_row("Total Trades", str(result.total_trades))
    table.add_row("Winning Trades", f"{result.winning_trades} ({result.win_rate:.1f}%)")
    table.add_row("Losing Trades", str(result.losing_trades))
    table.add_row("Profit Factor", f"{result.profit_factor:.2f}")

    # Risk metrics
    table.add_row("Max Drawdown", f"[red]${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)[/red]")
    table.add_row("Avg Win", f"[green]${result.avg_win:,.2f}[/green]")
    table.add_row("Avg Loss", f"[red]${result.avg_loss:,.2f}[/red]")
    table.add_row("Largest Win", f"[green]${result.largest_win:,.2f}[/green]")
    table.add_row("Largest Loss", f"[red]${result.largest_loss:,.2f}[/red]")

    console.print(table)

    # Show trades if detailed
    if detailed and result.trades:
        console.print("\n[cyan]Trade History:[/cyan]")
        trades_table = Table()
        trades_table.add_column("Timestamp", style="white")
        trades_table.add_column("Side", style="yellow")
        trades_table.add_column("Qty", style="white")
        trades_table.add_column("Price", style="cyan")
        trades_table.add_column("Total", style="green")

        for trade in result.trades:
            side_color = "green" if trade["side"] == "buy" else "red"
            trades_table.add_row(
                trade["timestamp"],
                f"[{side_color}]{trade['side'].upper()}[/{side_color}]",
                trade["qty"],
                f"${Decimal(trade['price']):,.2f}",
                f"${Decimal(trade['total']):,.2f}",
            )

        console.print(trades_table)


def _render_backtest_chart(
    result,
    data_source: str,
    historical_dir: Optional[str],
    chart_path: Optional[str],
    show: bool,
    theme: str,
) -> None:
    if not chart_path and not show:
        return

    from trader.visualization import build_backtest_chart, default_historical_data_dir

    resolved_dir = Path(historical_dir) if historical_dir else default_historical_data_dir()
    chart_builder = build_backtest_chart(
        result=result,
        data_source=data_source,
        data_dir=resolved_dir,
        theme=theme,
        include_price=True,
    )

    if chart_path:
        chart_builder.save_html(chart_path)
        console.print(f"[green]Chart saved to {chart_path}[/green]")

    if show:
        chart_builder.show()


def _parse_param_grid(param_entries: tuple[str, ...]) -> dict[str, list]:
    alias_map = {
        "trail_percent": "trailing_stop_pct",
        "trailing_pct": "trailing_stop_pct",
        "trailing_stop_pct": "trailing_stop_pct",
        "take_profit": "take_profit_pct",
        "take_profit_pct": "take_profit_pct",
        "stop_loss": "stop_loss_pct",
        "stop_loss_pct": "stop_loss_pct",
        "qty": "quantity",
        "quantity": "quantity",
    }
    grid: dict[str, list] = {}

    for entry in param_entries:
        if ":" not in entry:
            raise ValueError(f"Invalid param format: {entry}")
        key, raw_values = entry.split(":", 1)
        key = key.strip()
        if key not in alias_map:
            raise ValueError(f"Unknown parameter: {key}")
        canonical = alias_map[key]
        values = [v.strip() for v in raw_values.split(",") if v.strip()]
        if not values:
            raise ValueError(f"No values provided for {key}")

        parsed_values = []
        for value in values:
            if canonical == "quantity":
                parsed_values.append(int(value))
            else:
                parsed_values.append(Decimal(value))

        grid[canonical] = parsed_values

    return grid


def _validate_optimization_params(strategy_type: str, param_grid: dict[str, list]) -> None:
    if strategy_type == "trailing-stop":
        if "trailing_stop_pct" not in param_grid:
            raise ValueError("trailing_stop_pct is required for trailing-stop optimization")
    elif strategy_type == "bracket":
        if "take_profit_pct" not in param_grid or "stop_loss_pct" not in param_grid:
            raise ValueError("take_profit_pct and stop_loss_pct are required for bracket optimization")


def _display_optimization_result(result) -> None:
    table = Table(title=f"Optimization Results - {result.id}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Strategy", result.strategy_type)
    table.add_row("Symbol", result.symbol)
    table.add_row("Date Range", f"{result.start_date.date()} to {result.end_date.date()}")
    table.add_row("Objective", result.objective)
    table.add_row("Method", result.method)
    table.add_row("Combinations", str(result.num_combinations))
    table.add_row("Runtime (s)", f"{result.runtime_seconds:.2f}")
    table.add_row("Best Score", str(result.best_score))
    table.add_row("Best Params", str(result.best_params))

    console.print(table)


if __name__ == "__main__":
    cli()
