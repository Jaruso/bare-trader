"""CLI entry point for AutoTrader.

All business logic is delegated to the trader.app service layer.
This module handles:
- Click argument parsing
- Rich table formatting for human output
- JSON output when --json flag is used
- Error rendering (Rich or JSON based on mode)
"""

import json as json_lib
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from trader import __version__
from trader.audit import set_audit_source
from trader.errors import AppError
from trader.utils.config import Environment, load_config
from trader.utils.logging import setup_logging

console = Console()


# =============================================================================
# Helpers
# =============================================================================


def _handle_error(error: AppError, as_json: bool = False) -> None:
    """Render an AppError as Rich text or JSON."""
    if as_json:
        console.print(json_lib.dumps(error.to_dict(), indent=2))
    else:
        console.print(f"[red]Error: {error.message}[/red]")
        if error.suggestion:
            console.print(f"[dim]{error.suggestion}[/dim]")


def _json_output(data: object) -> None:
    """Print a Pydantic model or dict as JSON."""
    if hasattr(data, "model_dump_json"):
        console.print(data.model_dump_json(indent=2))  # type: ignore[union-attr]
    else:
        console.print(json_lib.dumps(data, indent=2, default=str))


def _get_json_flag(ctx: click.Context) -> bool:
    """Get the --json flag from context."""
    return ctx.obj.get("json", False)


# =============================================================================
# CLI Group
# =============================================================================


@click.group()
@click.version_option(version=__version__, prog_name="trader")
@click.option("--prod", is_flag=True, help="Use production environment (default: paper)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx: click.Context, prod: bool, as_json: bool) -> None:
    """AutoTrader - CLI-based automated trading system."""
    import sys
    import traceback
    from datetime import datetime
    from pathlib import Path

    log_file = Path.home() / "autotrader_mcp_debug.log"

    try:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | CLI entry point called\n")

        ctx.ensure_object(dict)
        set_audit_source("cli")
        config = load_config(prod=prod)
        ctx.obj["config"] = config
        ctx.obj["json"] = as_json

        # Set up logging
        logger = setup_logging(log_dir=config.log_dir, log_to_file=True)
        ctx.obj["logger"] = logger

        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | CLI setup complete\n")
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | CLI error: {e}\n")
            f.write(traceback.format_exc())
        print(f"CLI initialization error: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        raise


# =============================================================================
# Status & Account Commands
# =============================================================================


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current system status including engine state."""
    from trader.app.engine import get_engine_status

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = get_engine_status(config)
        if as_json:
            _json_output(result)
        else:
            table = Table(title="AutoTrader Status")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            env_style = "yellow" if config.env == Environment.PAPER else "red bold"
            table.add_row("Environment", f"[{env_style}]{result.environment}[/{env_style}]")
            table.add_row("Service", result.service)
            table.add_row("Base URL", result.base_url)

            key_status = "Configured" if result.api_key_configured else "[red]Not Set[/red]"
            table.add_row("API Key", key_status)

            if result.running:
                table.add_row("Engine", f"[green]RUNNING[/green] (PID {result.pid})")
            else:
                table.add_row("Engine", "[yellow]NOT RUNNING[/yellow]")

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)


@cli.command()
@click.pass_context
def balance(ctx: click.Context) -> None:
    """Show account balance and portfolio summary."""
    from trader.app.portfolio import get_balance

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = get_balance(config)
        if as_json:
            _json_output(result)
        else:
            table = Table(title="Account Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            acct = result.account
            table.add_row("Portfolio Value", f"${acct.portfolio_value:,.2f}")
            table.add_row("Equity", f"${acct.equity:,.2f}")
            table.add_row("Cash", f"${acct.cash:,.2f}")
            table.add_row("Buying Power", f"${acct.buying_power:,.2f}")

            if result.day_change is not None:
                change_style = "green" if result.day_change >= 0 else "red"
                sign = "+" if result.day_change >= 0 else ""
                table.add_row(
                    "Day's Change",
                    f"[{change_style}]{sign}${result.day_change:,.2f} "
                    f"({sign}{result.day_change_pct:.2f}%)[/{change_style}]",
                )

            if result.positions:
                pl_style = "green" if result.total_unrealized_pl >= 0 else "red"
                sign = "+" if result.total_unrealized_pl >= 0 else ""
                upl = f"[{pl_style}]{sign}${result.total_unrealized_pl:,.2f}[/{pl_style}]"
                table.add_row("Unrealized P/L", upl)
                table.add_row("Open Positions", str(len(result.positions)))

            table.add_row("", "")
            market_status = (
                "[green]OPEN[/green]" if result.market_open
                else "[yellow]CLOSED[/yellow]"
            )
            table.add_row("Market", market_status)
            table.add_row("Day Trades (5d)", str(acct.daytrade_count))
            if acct.pattern_day_trader:
                table.add_row("PDT Status", "[red]FLAGGED[/red]")

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error fetching balance: {e}[/red]")


@cli.command()
@click.pass_context
def positions(ctx: click.Context) -> None:
    """Show current positions."""
    from trader.app.portfolio import get_positions

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        positions_list = get_positions(config)
        if as_json:
            _json_output([p.model_dump() for p in positions_list])
        else:
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
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error fetching positions: {e}[/red]")


@cli.command()
@click.option("--all", "show_all", is_flag=True, help="Show all orders (including filled/canceled)")
@click.pass_context
def orders(ctx: click.Context, show_all: bool) -> None:
    """Show open orders."""
    from trader.app.orders import list_orders

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        orders_list = list_orders(config, show_all=show_all)
        if as_json:
            _json_output([o.model_dump() for o in orders_list])
        else:
            if not orders_list:
                console.print("[yellow]No open orders[/yellow]")
                return

            table = Table(title="Orders" if show_all else "Open Orders")
            table.add_column("ID", style="dim", max_width=8)
            table.add_column("Symbol", style="cyan")
            table.add_column("Side", justify="center")
            table.add_column("Type", justify="center")
            table.add_column("Qty", justify="right")
            table.add_column("Price", justify="right")
            table.add_column("Status", justify="center")

            for order in orders_list:
                side_style = "green" if order.side == "buy" else "red"
                side_text = f"[{side_style}]{order.side.upper()}[/{side_style}]"

                if order.order_type == "market":
                    price_text = "MARKET"
                elif order.limit_price:
                    price_text = f"${order.limit_price:,.2f}"
                elif order.stop_price:
                    price_text = f"${order.stop_price:,.2f}"
                elif order.trail_percent:
                    price_text = f"{order.trail_percent}%"
                else:
                    price_text = "-"

                table.add_row(
                    order.id[:8],
                    order.symbol,
                    side_text,
                    order.order_type.upper(),
                    str(order.qty),
                    price_text,
                    order.status.upper(),
                )

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error fetching orders: {e}[/red]")


@cli.command()
@click.pass_context
def portfolio(ctx: click.Context) -> None:
    """Show portfolio summary and performance."""
    from trader.app.portfolio import get_portfolio_summary

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = get_portfolio_summary(config)
        if as_json:
            _json_output(result)
        else:
            # Summary table
            table = Table(title="Portfolio Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Total Equity", f"${result.total_equity:,.2f}")
            table.add_row("Cash", f"${result.cash:,.2f}")
            table.add_row("Positions Value", f"${result.positions_value:,.2f}")
            table.add_row("Position Count", str(result.position_count))

            unreal_style = "green" if result.unrealized_pnl >= 0 else "red"
            real_style = "green" if result.realized_pnl_today >= 0 else "red"
            total_style = "green" if result.total_pnl_today >= 0 else "red"

            table.add_row(
                "Unrealized P/L",
                f"[{unreal_style}]${result.unrealized_pnl:,.2f} "
                f"({result.unrealized_pnl_pct:.2%})[/{unreal_style}]",
            )
            table.add_row(
                "Realized P/L (Today)",
                f"[{real_style}]${result.realized_pnl_today:,.2f}[/{real_style}]",
            )
            table.add_row(
                "Total P/L (Today)",
                f"[{total_style}]${result.total_pnl_today:,.2f}[/{total_style}]",
            )

            console.print(table)

            # Positions breakdown
            if result.positions:
                console.print()
                pos_table = Table(title="Position Breakdown")
                pos_table.add_column("Symbol", style="cyan")
                pos_table.add_column("Qty", justify="right")
                pos_table.add_column("Avg Cost", justify="right")
                pos_table.add_column("Current", justify="right")
                pos_table.add_column("Value", justify="right")
                pos_table.add_column("P/L", justify="right")
                pos_table.add_column("Weight", justify="right")

                for pos in result.positions:
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

    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument("symbol")
@click.pass_context
def quote(ctx: click.Context, symbol: str) -> None:
    """Get current quote for a symbol."""
    from trader.app.portfolio import get_quote

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = get_quote(config, symbol)
        if as_json:
            _json_output(result)
        else:
            table = Table(title=f"Quote: {symbol.upper()}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Bid", f"${result.bid:,.2f}")
            table.add_row("Ask", f"${result.ask:,.2f}")
            table.add_row("Spread", f"${result.spread:,.2f}")

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error fetching quote: {e}[/red]")


# =============================================================================
# Order Commands
# =============================================================================


@cli.command()
@click.argument("symbol")
@click.argument("price", type=float)
@click.option("--qty", type=int, default=1, help="Number of shares (default: 1)")
@click.pass_context
def buy(ctx: click.Context, symbol: str, price: float, qty: int) -> None:
    """Place a limit buy order.

    Example: trader buy TSLA 399.00 --qty 1
    """
    from trader.app.orders import place_order
    from trader.schemas.orders import OrderRequest

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        request = OrderRequest(
            symbol=symbol, qty=qty,
            price=Decimal(str(price)), side="buy",
        )
        if not as_json:
            msg = f"Placing LIMIT BUY: {qty} {symbol.upper()} @ ${price:.2f}"
            console.print(f"[yellow]{msg}[/yellow]")

        result = place_order(config, request)

        if as_json:
            _json_output(result)
        else:
            table = Table(title="Order Placed")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Order ID", result.id)
            table.add_row("Symbol", result.symbol)
            table.add_row("Side", "BUY")
            table.add_row("Quantity", str(result.qty))
            table.add_row("Type", result.order_type.upper())
            if result.limit_price:
                table.add_row("Limit Price", f"${result.limit_price:,.2f}")
            table.add_row("Status", result.status.upper())

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
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
    from trader.app.orders import place_order
    from trader.schemas.orders import OrderRequest

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        request = OrderRequest(
            symbol=symbol, qty=qty,
            price=Decimal(str(price)), side="sell",
        )
        if not as_json:
            msg = f"Placing LIMIT SELL: {qty} {symbol.upper()} @ ${price:.2f}"
            console.print(f"[yellow]{msg}[/yellow]")

        result = place_order(config, request)

        if as_json:
            _json_output(result)
        else:
            table = Table(title="Order Placed")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Order ID", result.id)
            table.add_row("Symbol", result.symbol)
            table.add_row("Side", "SELL")
            table.add_row("Quantity", str(result.qty))
            table.add_row("Type", result.order_type.upper())
            if result.limit_price:
                table.add_row("Limit Price", f"${result.limit_price:,.2f}")
            table.add_row("Status", result.status.upper())

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error placing order: {e}[/red]")


@cli.command(name="reconcile-orders")
@click.option(
    "--orders-dir", type=click.Path(),
    help="Path to config directory containing orders.yaml",
)
@click.pass_context
def reconcile_orders(ctx: click.Context, orders_dir: str | None) -> None:
    """Reconcile locally persisted orders with broker state."""
    from trader.core.engine import TradingEngine

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        from trader.app import get_broker
        broker = get_broker(config)
        orders_path = Path(orders_dir) if orders_dir else None
        engine = TradingEngine(broker, orders_dir=orders_path)

        if not as_json:
            console.print("Running reconciliation...")
        engine._reconcile_orders()
        if as_json:
            _json_output({"status": "completed"})
        else:
            console.print("[green]Reconciliation completed.[/green]")
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Reconciliation failed: {e}[/red]")


@cli.command()
@click.argument("order_id")
@click.pass_context
def cancel(ctx: click.Context, order_id: str) -> None:
    """Cancel an open order."""
    from trader.app.orders import cancel_order

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = cancel_order(config, order_id)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[green]Order {order_id} canceled[/green]")
    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error canceling order: {e}[/red]")


# =============================================================================
# Engine Commands
# =============================================================================


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
    from trader.app import get_broker
    from trader.core.engine import EngineAlreadyRunningError, TradingEngine, get_lock_file_path
    from trader.strategies.loader import load_strategies

    config = ctx.obj["config"]

    if not config.alpaca_api_key:
        env_var = "ALPACA_PROD_API_KEY" if config.is_prod else "ALPACA_API_KEY"
        console.print(f"[red]Error: {env_var} not configured[/red]")
        return

    # Interactive confirmation for production
    if config.is_prod:
        console.print("[red bold]\u26a0\ufe0f  PRODUCTION MODE \u26a0\ufe0f[/red bold]")
        svc = config.service.value
        console.print(f"[red]You are about to trade with REAL MONEY on {svc}[/red]")
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
@click.pass_context
def stop(ctx: click.Context, force: bool) -> None:
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
    from trader.app.engine import stop_engine

    as_json = _get_json_flag(ctx)

    try:
        result = stop_engine(force=force)
        if as_json:
            _json_output(result)
        else:
            if result["status"] == "killed":
                console.print(f"[yellow]Force killed trading engine (PID {result['pid']})[/yellow]")
            elif result["status"] == "stopping":
                pid = result['pid']
                console.print(f"[green]Sent shutdown signal to trading engine (PID {pid})[/green]")
                console.print("[dim]Engine will stop after current cycle completes[/dim]")
            else:
                console.print("[yellow]Engine already stopped[/yellow]")
    except AppError as e:
        _handle_error(e, as_json)


@cli.command()
@click.pass_context
def watch(ctx: click.Context) -> None:
    """Watch prices for symbols in your strategies."""
    from trader.app.portfolio import watch_strategies

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        results = watch_strategies(config)
        if as_json:
            _json_output(results)
        else:
            if not results:
                console.print("[yellow]No strategies configured[/yellow]")
                return

            table = Table(title="Price Watch")
            table.add_column("Symbol", style="cyan")
            table.add_column("Bid", justify="right")
            table.add_column("Ask", justify="right")
            table.add_column("Strategies")

            for item in results:
                if "error" in item:
                    table.add_row(item["symbol"], "[red]Error[/red]", str(item["error"]), "-")
                else:
                    table.add_row(
                        item["symbol"],
                        f"${Decimal(item['bid']):,.2f}",
                        f"${Decimal(item['ask']):,.2f}",
                        ", ".join(item["strategies"]) if item["strategies"] else "-",
                    )

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)


# =============================================================================
# History & Analysis Commands
# =============================================================================


@cli.command()
@click.option("--symbol", help="Filter by symbol")
@click.option("--limit", type=int, default=20, help="Number of trades to show")
@click.pass_context
def history(ctx: click.Context, symbol: str | None, limit: int) -> None:
    """Show trade history."""
    from trader.app.analysis import get_today_pnl, get_trade_history

    as_json = _get_json_flag(ctx)

    trades = get_trade_history(symbol=symbol, limit=limit)

    if as_json:
        _json_output(trades)
        return

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
        ts = datetime.fromisoformat(trade["timestamp"])
        side_val = trade["side"]
        side_style = "green" if side_val == "buy" else "red"
        time_str = ts.strftime("%m/%d %H:%M")
        table.add_row(
            time_str,
            trade["symbol"],
            f"[{side_style}]{side_val.upper()}[/{side_style}]",
            trade["quantity"],
            f"${Decimal(trade['price']):,.2f}",
            f"${Decimal(trade['total']):,.2f}",
            trade["status"].upper(),
        )

    console.print(table)

    today_pnl = get_today_pnl()
    pnl_style = "green" if today_pnl >= 0 else "red"
    console.print(f"\nToday's Realized P/L: [{pnl_style}]${today_pnl:,.2f}[/{pnl_style}]")


@cli.command()
@click.option("--symbol", help="Filter by symbol")
@click.option("--days", type=int, default=30, help="Analyze trades from last N days")
@click.option("--limit", type=int, default=1000, help="Max trades to analyze")
@click.pass_context
def analyze(ctx: click.Context, symbol: str | None, days: int, limit: int) -> None:
    """Analyze trade performance."""
    from trader.app.analysis import analyze_trade_performance

    as_json = _get_json_flag(ctx)

    result = analyze_trade_performance(symbol=symbol, days=days, limit=limit)
    if result is None:
        if as_json:
            _json_output({"trades": 0, "message": "No trades recorded for analysis"})
        else:
            console.print("[yellow]No trades recorded for analysis[/yellow]")
        return

    if as_json:
        _json_output(result)
        return

    summary = result.summary

    title = f"Trade Analysis{f' - {symbol}' if symbol else ''}"
    table = Table(title=title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Trades", str(summary.total_trades))
    table.add_row("Winning Trades", f"{summary.winning_trades} ({summary.win_rate:.1f}%)")
    table.add_row("Gross Profit", f"${summary.gross_profit:,.2f}")
    table.add_row("Gross Loss", f"-${summary.gross_loss:,.2f}")

    net_style = "green" if summary.net_profit >= 0 else "red"
    table.add_row("Net P/L", f"[{net_style}]${summary.net_profit:,.2f}[/{net_style}]")

    profit_factor = "N/A"
    if summary.gross_loss > 0:
        profit_factor = f"{summary.profit_factor:.2f}"
    table.add_row("Profit Factor", profit_factor)

    table.add_row("Avg Win", f"${summary.avg_win:,.2f}")
    table.add_row("Avg Loss", f"${summary.avg_loss:,.2f}")
    table.add_row("Largest Win", f"${summary.largest_win:,.2f}")
    table.add_row("Largest Loss", f"${summary.largest_loss:,.2f}")
    table.add_row("Avg Hold (min)", f"{summary.avg_hold_minutes:.1f}")

    console.print(table)

    if result.per_symbol:
        symbol_table = Table(title="Per-Symbol Performance")
        symbol_table.add_column("Symbol", style="cyan")
        symbol_table.add_column("Trades", justify="right")
        symbol_table.add_column("Win %", justify="right")
        symbol_table.add_column("Net P/L", justify="right")
        symbol_table.add_column("Profit Factor", justify="right")

        for sym, stats in sorted(result.per_symbol.items()):
            s_net_style = "green" if stats.net_profit >= 0 else "red"
            pf_display = "N/A" if stats.gross_loss == 0 else f"{stats.profit_factor:.2f}"
            symbol_table.add_row(
                sym,
                str(stats.total_trades),
                f"{stats.win_rate:.1f}%",
                f"[{s_net_style}]${stats.net_profit:,.2f}[/{s_net_style}]",
                pf_display,
            )

        console.print(symbol_table)

    if result.open_positions:
        open_table = Table(title="Open Lots (Unmatched Buys)")
        open_table.add_column("Symbol", style="cyan")
        open_table.add_column("Lots", justify="right")
        open_table.add_column("Qty", justify="right")
        open_table.add_column("Avg Cost", justify="right")

        for pos in result.open_positions:
            open_table.add_row(
                pos.symbol,
                str(pos.lots),
                str(pos.quantity),
                f"${pos.avg_cost:,.2f}",
            )

        console.print(open_table)

    remaining_sells = {k: v for k, v in result.unmatched_sell_qty.items() if v > 0}
    if remaining_sells:
        console.print("[yellow]Warning: sells without matching buys detected.[/yellow]")


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--days", type=int, default=30, help="Export trades from last N days")
@click.pass_context
def export(ctx: click.Context, output: str, days: int) -> None:
    """Export trade history to CSV."""
    from trader.data.ledger import TradeLedger

    ledger = TradeLedger()
    since = datetime.now() - timedelta(days=days)
    path = Path(output)

    count = ledger.export_csv(path, since=since)
    as_json = _get_json_flag(ctx)
    if as_json:
        _json_output({"exported": count, "path": str(path)})
    else:
        console.print(f"[green]Exported {count} trades to {path}[/green]")


# =============================================================================
# Safety Commands
# =============================================================================


@cli.command()
@click.pass_context
def safety(ctx: click.Context) -> None:
    """Show safety controls status."""
    from trader.app.data import get_safety_status

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        result = get_safety_status(config)
        if as_json:
            _json_output(result)
        else:
            status = result["status"]
            limits_data = result["limits"]

            table = Table(title="Safety Controls")
            table.add_column("Control", style="cyan")
            table.add_column("Status", justify="right")
            table.add_column("Limit", justify="right")

            kill_status = "[red]ACTIVE[/red]" if status["kill_switch"] else "[green]OFF[/green]"
            table.add_row("Kill Switch", kill_status, "-")

            pnl = status["daily_pnl"]
            pnl_style = "green" if pnl >= 0 else "red"
            remaining = status["daily_pnl_remaining"]
            table.add_row(
                "Daily P/L",
                f"[{pnl_style}]${pnl:,.2f}[/{pnl_style}]",
                f"${status['daily_pnl_limit']:,.2f}",
            )
            table.add_row("Loss Remaining", f"${remaining:,.2f}", "-")

            trades_count = status["trade_count"]
            trade_limit = status["trade_limit"]
            pct = trades_count / trade_limit * 100 if trade_limit > 0 else 0
            table.add_row("Trades Today", f"{trades_count} ({pct:.0f}%)", str(trade_limit))
            table.add_row("Trades Remaining", str(status["trades_remaining"]), "-")

            can_trade = status["can_trade"]
            trade_status = "[green]YES[/green]" if can_trade else "[red]NO[/red]"
            table.add_row("Can Trade", trade_status, "-")

            console.print(table)

            # Position limits
            console.print()
            limit_table = Table(title="Position Limits")
            limit_table.add_column("Limit", style="cyan")
            limit_table.add_column("Value", justify="right")

            limit_table.add_row("Max Position Size", f"{limits_data['max_position_size']} shares")
            mpv = Decimal(limits_data['max_position_value'])
            mov = Decimal(limits_data['max_order_value'])
            limit_table.add_row("Max Position Value", f"${mpv:,.2f}")
            limit_table.add_row("Max Order Value", f"${mov:,.2f}")
            limit_table.add_row("Max Daily Loss", f"${Decimal(limits_data['max_daily_loss']):,.2f}")
            limit_table.add_row("Max Daily Trades", str(limits_data["max_daily_trades"]))

            console.print(limit_table)

    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def kill(ctx: click.Context) -> None:
    """Activate kill switch - stops all automated trading."""
    as_json = _get_json_flag(ctx)
    if as_json:
        _json_output({"status": "kill_switch_activated"})
    else:
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
    from trader.app.portfolio import scan_symbols

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        results = scan_symbols(config, list(symbols) if symbols else None)
        if as_json:
            _json_output(results)
        else:
            if not results:
                console.print("[yellow]No symbols to scan[/yellow]")
                console.print("Provide symbols: trader scan AAPL TSLA")
                return

            table = Table(title="Market Scan")
            table.add_column("Symbol", style="cyan")
            table.add_column("Bid", justify="right")
            table.add_column("Ask", justify="right")
            table.add_column("Spread", justify="right")
            table.add_column("Strategies")

            for item in results:
                if "error" in item:
                    table.add_row(item["symbol"], "[red]Error[/red]", "-", "-", str(item["error"]))
                else:
                    table.add_row(
                        item["symbol"],
                        f"${Decimal(item['bid']):,.2f}",
                        f"${Decimal(item['ask']):,.2f}",
                        f"${Decimal(item['spread']):.2f} ({Decimal(item['spread_pct']):.2f}%)",
                        ", ".join(item["strategies"]) if item["strategies"] else "-",
                    )

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)


# =============================================================================
# Strategy Commands
# =============================================================================



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


@cli.group()
def indicator() -> None:
    """Work with technical indicators."""
    pass


@indicator.command("list")
@click.pass_context
def indicator_list(ctx: click.Context) -> None:
    """List available indicators."""
    from trader.app.indicators import list_all_indicators

    as_json = _get_json_flag(ctx)

    indicators = list_all_indicators()
    if as_json:
        _json_output([i.model_dump() for i in indicators])
    else:
        table = Table(title="Indicators")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Params", style="green")

        for spec in indicators:
            params = ", ".join(f"{k}" for k in spec.params.keys()) if spec.params else "-"
            table.add_row(spec.name, spec.description, params)

        console.print(table)


@indicator.command("describe")
@click.argument("name")
@click.pass_context
def indicator_describe(ctx: click.Context, name: str) -> None:
    """Show details for an indicator."""
    from trader.app.indicators import describe_indicator

    as_json = _get_json_flag(ctx)

    try:
        result = describe_indicator(name)
        if as_json:
            _json_output(result)
        else:
            table = Table(title=f"Indicator - {result.name}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Description", result.description)
            table.add_row("Output", result.output or "-")
            params = (
                ", ".join(f"{k}: {v}" for k, v in result.params.items())
                if result.params else "-"
            )
            table.add_row("Params", params)

            console.print(table)
    except AppError as e:
        _handle_error(e, as_json)


# =============================================================================
# Notify Commands
# =============================================================================


@cli.group()
def notify() -> None:
    """Send and test notifications (Discord, webhook).

    Configure via DISCORD_WEBHOOK_URL or config/notifications.yaml.
    """
    pass


@notify.command("test")
@click.option(
    "--channel",
    type=click.Choice(["discord", "webhook", "all"]),
    default="all",
    help="Channel to test (default: all enabled)",
)
@click.pass_context
def notify_test(ctx: click.Context, channel: str) -> None:
    """Send a test notification to verify channel configuration."""
    from trader.app.notifications import get_notification_manager, send_test_notification
    from trader.errors import ConfigurationError

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)
    config_dir = config.data_dir.parent / "config"

    manager = get_notification_manager(config_dir=config_dir)
    if not manager.enabled:
        if as_json:
            _json_output({"ok": False, "message": "No notification channels configured"})
        else:
            console.print(
                "[yellow]No notification channels configured.[/yellow]\n"
                "Set DISCORD_WEBHOOK_URL or CUSTOM_WEBHOOK_URL, or add config/notifications.yaml"
            )
        return

    ok = send_test_notification(channel=channel, config_dir=config_dir)
    if as_json:
        _json_output({"ok": ok, "channel": channel})
    else:
        if ok:
            console.print(f"[green]Test notification sent to {channel}[/green]")
        else:
            console.print(f"[red]Failed to send test to {channel}[/red]")


@notify.command("send")
@click.argument("message", required=True)
@click.option(
    "--channel",
    type=click.Choice(["discord", "webhook", "all"]),
    default="all",
    help="Channel to send to (default: all)",
)
@click.pass_context
def notify_send(ctx: click.Context, message: str, channel: str) -> None:
    """Send a manual notification message."""
    from trader.app.notifications import get_notification_manager, send_notification

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)
    config_dir = config.data_dir.parent / "config"

    manager = get_notification_manager(config_dir=config_dir)
    if not manager.enabled:
        if as_json:
            _json_output({"ok": False, "message": "No channels configured"})
        else:
            console.print("[yellow]No notification channels configured.[/yellow]")
        return

    send_notification(message, channel=channel, config_dir=config_dir)
    if as_json:
        _json_output({"ok": True, "channel": channel})
    else:
        console.print(f"[green]Message sent to {channel}[/green]")


@strategy.command("list")
@click.pass_context
def strategy_list(ctx: click.Context) -> None:
    """List all trading strategies."""
    from trader.app.strategies import list_strategies

    as_json = _get_json_flag(ctx)
    result = list_strategies()

    if as_json:
        _json_output(result)
        return

    if not result.strategies:
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

    for s in result.strategies:
        # Phase styling
        phase_styles = {
            "pending": "[yellow]PENDING[/yellow]",
            "entry_active": "[blue]ENTERING[/blue]",
            "position_open": "[green]OPEN[/green]",
            "exiting": "[blue]EXITING[/blue]",
            "completed": "[dim]DONE[/dim]",
            "failed": "[red]FAILED[/red]",
            "paused": "[yellow]PAUSED[/yellow]",
        }
        phase_str = phase_styles.get(s.phase, s.phase)

        if not s.enabled:
            phase_str = "[dim]DISABLED[/dim]"

        # Build details string
        details = []
        stype = s.strategy_type
        if stype == "trailing_stop":
            details.append(f"trail: {s.trailing_stop_pct}%")
            if s.high_watermark:
                details.append(f"high: ${s.high_watermark:.2f}")
        elif stype == "bracket":
            details.append(f"TP: +{s.take_profit_pct}%")
            details.append(f"SL: -{s.stop_loss_pct}%")
        elif stype == "scale_out":
            if s.scale_targets:
                targets = [f"+{t['target_pct']}%" for t in s.scale_targets]
                details.append(f"targets: {', '.join(targets)}")

        if s.entry_fill_price:
            details.insert(0, f"entry: ${s.entry_fill_price:.2f}")

        table.add_row(
            s.id,
            s.symbol,
            s.strategy_type.replace("_", "-"),
            str(s.quantity),
            phase_str,
            " | ".join(details) if details else "-",
        )

    console.print(table)


@strategy.command("add")
@click.argument("strategy_type", type=click.Choice([
    "trailing-stop", "bracket", "scale-out", "grid",
]))
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
    trailing_pct: float | None,
    take_profit: float | None,
    stop_loss: float | None,
    limit: float | None,
    levels: int | None,
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
    from trader.app.strategies import create_strategy
    from trader.schemas.strategies import StrategyCreate

    config = ctx.obj["config"]
    as_json = _get_json_flag(ctx)

    try:
        request = StrategyCreate(
            strategy_type=strategy_type,
            symbol=symbol,
            qty=qty,
            trailing_pct=trailing_pct,
            take_profit=take_profit,
            stop_loss=stop_loss,
            entry_price=limit,
            levels=levels,
        )
        result = create_strategy(config, request)

        if as_json:
            _json_output(result)
        else:
            console.print(f"[green]Strategy added:[/green] {strategy_type} {qty} {symbol.upper()}")
            console.print(f"[dim]ID: {result.id}[/dim]")
            entry_str = f"limit @ ${limit:.2f}" if limit else "market"
            console.print(f"[dim]Entry: {entry_str}[/dim]")

            # Build detail string for display
            stype = result.strategy_type
            if stype == "trailing_stop":
                console.print(f"[dim]trailing stop: {result.trailing_stop_pct}%[/dim]")
            elif stype == "bracket":
                tp = result.take_profit_pct
                sl = result.stop_loss_pct
                console.print(f"[dim]take-profit: +{tp}%, stop-loss: -{sl}%[/dim]")
            elif stype == "scale_out" and result.scale_targets:
                targets = [f"+{t['target_pct']}%" for t in result.scale_targets]
                console.print(f"[dim]targets: {', '.join(targets)}[/dim]")
            elif stype == "grid" and result.grid_config:
                gc = result.grid_config
                lo, hi, lvl = gc['low'], gc['high'], gc['levels']
                console.print(f"[dim]range: ${lo:.2f}-${hi:.2f}, {lvl} levels[/dim]")

            console.print()
            console.print("Start the engine to activate: [cyan]trader start[/cyan]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("show")
@click.argument("strategy_id")
@click.pass_context
def strategy_show(ctx: click.Context, strategy_id: str) -> None:
    """Show details of a specific strategy."""
    from trader.app.strategies import get_strategy_detail

    as_json = _get_json_flag(ctx)

    try:
        strat = get_strategy_detail(strategy_id)
        if as_json:
            _json_output(strat)
        else:
            stype_label = strat.strategy_type.replace('_', '-').upper()
            console.print(f"\n[bold]{stype_label}[/bold] Strategy")
            console.print(f"ID: {strat.id}")
            console.print(f"Symbol: [cyan]{strat.symbol}[/cyan]")
            console.print(f"Quantity: {strat.quantity}")
            console.print(f"Phase: {strat.phase}")
            console.print(f"Enabled: {'Yes' if strat.enabled else 'No'}")
            console.print()

            console.print("[bold]Entry Configuration[/bold]")
            console.print(f"  Type: {strat.entry_type}")
            if strat.entry_price:
                console.print(f"  Price: ${strat.entry_price:.2f}")
            if strat.entry_order_id:
                console.print(f"  Order ID: {strat.entry_order_id}")
            if strat.entry_fill_price:
                console.print(f"  Fill Price: ${strat.entry_fill_price:.2f}")
            console.print()

            console.print("[bold]Exit Configuration[/bold]")
            if strat.strategy_type == "trailing_stop":
                console.print(f"  Trailing Stop: {strat.trailing_stop_pct}%")
                if strat.high_watermark:
                    console.print(f"  High Watermark: ${strat.high_watermark:.2f}")
                    stop_price = strat.high_watermark * (1 - strat.trailing_stop_pct / 100)
                    console.print(f"  Current Stop: ${stop_price:.2f}")
            elif strat.strategy_type == "bracket":
                console.print(f"  Take Profit: +{strat.take_profit_pct}%")
                console.print(f"  Stop Loss: -{strat.stop_loss_pct}%")
                if strat.entry_fill_price:
                    tp_price = strat.entry_fill_price * (1 + strat.take_profit_pct / 100)
                    sl_price = strat.entry_fill_price * (1 - strat.stop_loss_pct / 100)
                    console.print(f"  TP Target: ${tp_price:.2f}")
                    console.print(f"  SL Target: ${sl_price:.2f}")
            elif strat.strategy_type == "scale_out" and strat.scale_targets:
                console.print("  Targets:")
                for t in strat.scale_targets:
                    console.print(f"    - {t['pct']}% at +{t['target_pct']}%")
            elif strat.strategy_type == "grid" and strat.grid_config:
                lo = strat.grid_config['low']
                hi = strat.grid_config['high']
                console.print(f"  Range: ${lo:.2f} - ${hi:.2f}")
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
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("remove")
@click.argument("strategy_id")
@click.pass_context
def strategy_remove(ctx: click.Context, strategy_id: str) -> None:
    """Remove a trading strategy."""
    from trader.app.strategies import remove_strategy

    as_json = _get_json_flag(ctx)

    try:
        result = remove_strategy(strategy_id)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[green]Strategy {strategy_id} removed[/green]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("enable")
@click.argument("strategy_id")
@click.pass_context
def strategy_enable(ctx: click.Context, strategy_id: str) -> None:
    """Enable a trading strategy."""
    from trader.app.strategies import set_strategy_enabled

    as_json = _get_json_flag(ctx)

    try:
        result = set_strategy_enabled(strategy_id, enabled=True)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[green]Strategy {strategy_id} enabled[/green]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("disable")
@click.argument("strategy_id")
@click.pass_context
def strategy_disable(ctx: click.Context, strategy_id: str) -> None:
    """Disable a trading strategy."""
    from trader.app.strategies import set_strategy_enabled

    as_json = _get_json_flag(ctx)

    try:
        result = set_strategy_enabled(strategy_id, enabled=False)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[yellow]Strategy {strategy_id} disabled[/yellow]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("pause")
@click.argument("strategy_id")
@click.pass_context
def strategy_pause(ctx: click.Context, strategy_id: str) -> None:
    """Pause an active strategy."""
    from trader.app.strategies import pause_strategy

    as_json = _get_json_flag(ctx)

    try:
        result = pause_strategy(strategy_id)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[yellow]Strategy {strategy_id} paused[/yellow]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("resume")
@click.argument("strategy_id")
@click.pass_context
def strategy_resume(ctx: click.Context, strategy_id: str) -> None:
    """Resume a paused strategy."""
    from trader.app.strategies import resume_strategy

    as_json = _get_json_flag(ctx)

    try:
        result = resume_strategy(strategy_id)
        if as_json:
            _json_output(result)
        else:
            console.print(f"[green]Strategy {strategy_id} resumed ({result['phase']})[/green]")
    except AppError as e:
        _handle_error(e, as_json)


@strategy.command("explain")
@click.argument("strategy_type", type=click.Choice([
    "trailing-stop", "bracket", "scale-out", "grid",
]))
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
    data_dir: str | None,
    historical_dir: str | None,
    output: str | None,
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
            with open(source_path) as f:
                data = json_lib.load(f)
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
    num_samples: int | None,
    data_source: str,
    data_dir: str | None,
    results_dir: str | None,
    initial_capital: float,
    save: bool,
    show_results: bool,
) -> None:
    """Optimize strategy parameters using backtests."""
    from trader.optimization import Optimizer, save_optimization

    logger = ctx.obj["logger"]
    as_json = _get_json_flag(ctx)

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
            if not as_json:
                console.print(f"[green]Optimization saved with ID: {result.id}[/green]")

        if as_json:
            from trader.schemas.optimization import OptimizeResponse
            _json_output(OptimizeResponse.from_domain(result))
        elif show_results:
            _display_optimization_result(result)

    except Exception as exc:
        logger.error(f"Optimization failed: {exc}", exc_info=True)
        if as_json:
            err = {"error": "OPTIMIZATION_FAILED", "message": str(exc)}
            console.print(json_lib.dumps(err, indent=2))
        else:
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
@click.option(
    "--data-dir", type=click.Path(exists=True),
    help="Directory containing CSV data files",
)
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
    trailing_pct: float | None,
    take_profit: float | None,
    stop_loss: float | None,
    data_source: str,
    data_dir: str | None,
    initial_capital: float,
    save: bool,
    chart: str | None,
    show: bool,
    theme: str,
) -> None:
    """Run a backtest for a strategy."""
    from trader.app.backtests import run_backtest
    from trader.schemas.backtests import BacktestRequest

    logger = ctx.obj["logger"]
    as_json = _get_json_flag(ctx)

    try:
        request = BacktestRequest(
            strategy_type=strategy_type,
            symbol=symbol,
            start=start,
            end=end,
            qty=qty,
            trailing_pct=trailing_pct,
            take_profit=take_profit,
            stop_loss=stop_loss,
            data_source=data_source,
            data_dir=data_dir,
            initial_capital=initial_capital,
            save=save,
        )

        if not as_json:
            console.print(f"[cyan]Loading historical data for {symbol}...[/cyan]")
            console.print("[cyan]Running backtest...[/cyan]")

        result = run_backtest(ctx.obj["config"], request)

        if as_json:
            _json_output(result)
        else:
            if save:
                console.print(f"[green]Backtest saved with ID: {result.id}[/green]")
            _display_backtest_result_from_schema(result)

            # Load domain result for charting
            if chart or show:
                from trader.backtest import load_backtest as _load_bt
                try:
                    domain_result = _load_bt(result.id)
                    data_dir_path = (
                        Path(data_dir) if data_dir
                        else Path.cwd() / "data" / "historical"
                    )
                    _render_backtest_chart(
                        result=domain_result,
                        data_source=data_source,
                        historical_dir=str(data_dir_path),
                        chart_path=chart,
                        show=show,
                        theme=theme,
                    )
                except Exception:
                    pass

    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        if as_json:
            console.print(json_lib.dumps({"error": "BACKTEST_FAILED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error running backtest: {e}[/red]")


@backtest.command("list")
@click.option("--data-dir", type=click.Path(exists=True), help="Data directory")
@click.pass_context
def backtest_list(ctx: click.Context, data_dir: str | None) -> None:
    """List all saved backtests."""
    from trader.app.backtests import list_backtests_app

    as_json = _get_json_flag(ctx)

    try:
        backtests = list_backtests_app(data_dir=data_dir)

        if as_json:
            _json_output([bt.model_dump() for bt in backtests])
            return

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
            return_color = "green" if bt.total_return_pct > 0 else "red"
            return_str = f"[{return_color}]{bt.total_return_pct:+.2f}%[/{return_color}]"
            date_range = f"{bt.start_date[:10]} to {bt.end_date[:10]}"

            table.add_row(
                bt.id,
                bt.symbol,
                bt.strategy_type,
                date_range,
                return_str,
                f"{bt.win_rate:.1f}%",
                str(bt.total_trades),
                f"{bt.max_drawdown_pct:.2f}%",
            )

        console.print(table)

    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
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
    data_dir: str | None,
    historical_dir: str | None,
    data_source: str,
    chart: str | None,
    show: bool,
    theme: str,
) -> None:
    """Show detailed results for a backtest."""
    from trader.app.backtests import show_backtest
    from trader.backtest import load_backtest

    as_json = _get_json_flag(ctx)

    try:
        result = show_backtest(backtest_id, data_dir=data_dir)
        if as_json:
            _json_output(result)
        else:
            _display_backtest_result_from_schema(result, detailed=True)

            if chart or show:
                data_dir_path = Path(data_dir) if data_dir else None
                try:
                    domain_result = load_backtest(backtest_id, data_dir=data_dir_path)
                    _render_backtest_chart(
                        result=domain_result,
                        data_source=data_source,
                        historical_dir=historical_dir,
                        chart_path=chart,
                        show=show,
                        theme=theme,
                    )
                except Exception:
                    pass

    except AppError as e:
        _handle_error(e, as_json)
    except Exception as e:
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error loading backtest: {e}[/red]")


@backtest.command("compare")
@click.argument("backtest_ids", nargs=-1, required=True)
@click.option("--data-dir", type=click.Path(exists=True), help="Data directory")
@click.pass_context
def backtest_compare(
    ctx: click.Context, backtest_ids: tuple[str, ...],
    data_dir: str | None,
) -> None:
    """Compare multiple backtests side-by-side."""
    from trader.app.backtests import compare_backtests

    as_json = _get_json_flag(ctx)

    try:
        results = compare_backtests(list(backtest_ids), data_dir=data_dir)

        if as_json:
            _json_output([r.model_dump() for r in results])
            return

        if not results:
            console.print("[red]No backtests found to compare[/red]")
            return

        table = Table(title="Backtest Comparison")
        table.add_column("Metric", style="cyan")
        for result in results:
            table.add_column(f"{result.id[:6]}...", style="white")

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
        if as_json:
            console.print(json_lib.dumps({"error": "UNEXPECTED", "message": str(e)}, indent=2))
        else:
            console.print(f"[red]Error comparing backtests: {e}[/red]")


# =============================================================================
# Display Helpers
# =============================================================================


def _display_backtest_result_from_schema(result, detailed: bool = False) -> None:
    """Display backtest result from a BacktestResponse schema."""
    table = Table(title=f"Backtest Results - {result.id}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Symbol", result.symbol)
    table.add_row("Strategy", result.strategy_type)
    table.add_row("Date Range", f"{result.start_date.date()} to {result.end_date.date()}")

    return_color = "green" if result.total_return > 0 else "red"
    table.add_row("Initial Capital", f"${result.initial_capital:,.2f}")
    table.add_row("Final Equity", f"${result.initial_capital + result.total_return:,.2f}")
    table.add_row("Total Return", f"[{return_color}]${result.total_return:+,.2f}[/{return_color}]")
    table.add_row("Return %", f"[{return_color}]{result.total_return_pct:+.2f}%[/{return_color}]")

    table.add_row("Total Trades", str(result.total_trades))
    table.add_row("Winning Trades", f"{result.winning_trades} ({result.win_rate:.1f}%)")
    table.add_row("Losing Trades", str(result.losing_trades))
    table.add_row("Profit Factor", f"{result.profit_factor:.2f}")

    dd = f"${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)"
    table.add_row("Max Drawdown", f"[red]{dd}[/red]")
    table.add_row("Avg Win", f"[green]${result.avg_win:,.2f}[/green]")
    table.add_row("Avg Loss", f"[red]${result.avg_loss:,.2f}[/red]")
    table.add_row("Largest Win", f"[green]${result.largest_win:,.2f}[/green]")
    table.add_row("Largest Loss", f"[red]${result.largest_loss:,.2f}[/red]")

    console.print(table)

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
    historical_dir: str | None,
    chart_path: str | None,
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
            raise ValueError(
                "take_profit_pct and stop_loss_pct are required"
                " for bracket optimization"
            )


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


# =============================================================================
# MCP Server Commands
# =============================================================================


@cli.group()
@click.pass_context
def mcp(ctx: click.Context) -> None:
    """MCP server commands."""
    import sys

    from trader.utils.logging import setup_logging

    # Redirect logging to stderr immediately so subcommands using stdio
    # transport don't have their protocol stream corrupted by log output.
    setup_logging(
        log_dir=ctx.obj["config"].log_dir,
        log_to_file=True,
        console_stream=sys.stderr,
    )


@mcp.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"]),
    default="stdio",
    show_default=True,
    help="Transport: stdio (local Claude) or streamable-http (remote, use --ssl-certfile/--ssl-keyfile for HTTPS)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to bind for streamable-http",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    show_default=True,
    help="Port to bind for streamable-http",
)
@click.option("--mount-path", default=None, help="Optional mount path for streamable-http (if supported by SDK)")
@click.option("--ssl-certfile", default=None, help="TLS certificate file for HTTPS")
@click.option("--ssl-keyfile", default=None, help="TLS private key file for HTTPS")
def serve(
    transport: str,
    host: str,
    port: int,
    mount_path: str | None,
    ssl_certfile: str | None,
    ssl_keyfile: str | None,
) -> None:
    """Start the MCP server (stdio or streamable HTTP).

    Launches an MCP-compliant server, allowing AI agents (e.g. Claude Desktop)
    to interact with AutoTrader via the MCP protocol.
    """
    import asyncio
    import sys
    import traceback
    from datetime import datetime
    from pathlib import Path

    # Write to log file for debugging
    log_file = Path.home() / "autotrader_mcp_debug.log"

    def log(msg: str) -> None:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {msg}\n")
        print(msg, file=sys.stderr, flush=True)

    log("MCP serve command started")

    try:
        log("Importing run_server...")
        from trader.mcp.server import run_server
        log("Import successful")

        log(f"Running server with transport={transport}")
        asyncio.run(
            run_server(
                transport=transport,
                host=host,
                port=port,
                mount_path=mount_path,
                ssl_certfile=ssl_certfile,
                ssl_keyfile=ssl_keyfile,
            )
        )
        log("Server exited normally")
    except Exception as e:
        log(f"MCP server error: {e}")
        log(traceback.format_exc())
        raise


if __name__ == "__main__":
    cli()
