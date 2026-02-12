"""MCP server for AutoTrader.

Uses the official MCP Python SDK (FastMCP) with stdio or HTTP transports.
Tools delegate to the trader.app service layer and return JSON responses.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from trader.errors import AppError, ValidationError

# =============================================================================
# Helpers
# =============================================================================


def _config() -> Any:
    """Load config lazily (avoids import-time side effects)."""
    from trader.utils.config import load_config

    return load_config()


def _ok(data: object) -> str:
    """Serialize a Pydantic model or dict/list to JSON."""
    if hasattr(data, "model_dump_json"):
        return str(data.model_dump_json(indent=2))
    return json.dumps(data, indent=2, default=str)


def _err(e: AppError) -> str:
    """Serialize an AppError to JSON."""
    return json.dumps(e.to_dict(), indent=2)


# =============================================================================
# Engine Tools
# =============================================================================


def get_status() -> str:
    """Get current AutoTrader engine status.

    Returns engine running state, environment (paper/prod),
    broker service, API key configuration, active strategy count,
    and process ID if running. Check the 'hint' field for actionable
    guidance when the engine is not running or misconfigured.
    """
    from trader.app.engine import get_engine_status

    try:
        return _ok(get_engine_status(_config()))
    except AppError as e:
        return _err(e)


def stop_engine(force: bool = False) -> str:
    """Stop the running trading engine.

    Args:
        force: If true, send SIGKILL instead of SIGTERM.
    """
    from trader.app.engine import stop_engine as _stop_engine

    try:
        return _ok(_stop_engine(force=force))
    except AppError as e:
        return _err(e)


# =============================================================================
# Portfolio & Market Data Tools
# =============================================================================


def get_balance() -> str:
    """Get account balance, equity, buying power, and daily P/L."""
    from trader.app.portfolio import get_balance as _get_balance

    try:
        return _ok(_get_balance(_config()))
    except AppError as e:
        return _err(e)


def get_positions() -> str:
    """List all open positions with current prices and unrealized P/L."""
    from trader.app.portfolio import get_positions as _get_positions

    try:
        result = _get_positions(_config())
        return json.dumps(
            [p.model_dump() for p in result], indent=2, default=str
        )
    except AppError as e:
        return _err(e)


def get_portfolio() -> str:
    """Get detailed portfolio summary with position weights and P/L breakdown."""
    from trader.app.portfolio import get_portfolio_summary

    try:
        return _ok(get_portfolio_summary(_config()))
    except AppError as e:
        return _err(e)


def get_quote(symbol: str) -> str:
    """Get current bid/ask/last quote for a symbol.

    Args:
        symbol: Stock ticker (e.g. "AAPL", "MSFT").
    """
    from trader.app.portfolio import get_quote as _get_quote

    try:
        return _ok(_get_quote(_config(), symbol.upper()))
    except AppError as e:
        return _err(e)


def get_top_movers(market_type: str = "stocks", limit: int = 10) -> str:
    """Get top market movers (gainers and losers).

    Args:
        market_type: Market type ('stocks' or 'crypto'). Defaults to 'stocks'.
        limit: Maximum number of gainers/losers to return. Defaults to 10.
    """
    from trader.app.portfolio import get_top_movers as _get_top_movers

    try:
        result = _get_top_movers(_config(), market_type=market_type, limit=limit)
        return json.dumps(result, indent=2, default=str)
    except AppError as e:
        return _err(e)


# =============================================================================
# Order Tools
# =============================================================================


def place_order(symbol: str, qty: int, side: str, price: float) -> str:
    """Place a limit order (with safety checks).

    Args:
        symbol: Stock ticker (e.g. "AAPL").
        qty: Number of shares (must be >= 1).
        side: "buy" or "sell".
        price: Limit price per share.
    """
    from trader.app.orders import place_order as _place_order
    from trader.schemas.orders import OrderRequest

    try:
        request = OrderRequest(
            symbol=symbol.upper(),
            qty=qty,
            side=side.lower(),
            price=Decimal(str(price)),
        )
        return _ok(_place_order(_config(), request))
    except AppError as e:
        return _err(e)


def list_orders(show_all: bool = False) -> str:
    """List orders. By default shows only open/pending orders.

    Args:
        show_all: If true, include filled, cancelled, and expired orders.
    """
    from trader.app.orders import list_orders as _list_orders

    try:
        result = _list_orders(_config(), show_all=show_all)
        return json.dumps(
            [o.model_dump() for o in result], indent=2, default=str
        )
    except AppError as e:
        return _err(e)


def cancel_order(order_id: str) -> str:
    """Cancel an open order by ID.

    Args:
        order_id: The order ID to cancel.
    """
    from trader.app.orders import cancel_order as _cancel_order

    try:
        return _ok(_cancel_order(_config(), order_id))
    except AppError as e:
        return _err(e)


# =============================================================================
# Strategy Tools
# =============================================================================


def list_strategies() -> str:
    """List all configured trading strategies."""
    from trader.app.strategies import list_strategies as _list_strategies

    try:
        return _ok(_list_strategies())
    except AppError as e:
        return _err(e)


def get_strategy(strategy_id: str) -> str:
    """Get detailed information about a specific strategy.

    Args:
        strategy_id: The strategy ID.
    """
    from trader.app.strategies import get_strategy_detail

    try:
        return _ok(get_strategy_detail(strategy_id))
    except AppError as e:
        return _err(e)


def create_strategy(
    strategy_type: str,
    symbol: str,
    qty: int = 1,
    trailing_pct: float | None = None,
    pullback_pct: float | None = None,
    take_profit: float | None = None,
    stop_loss: float | None = None,
    entry_price: float | None = None,
    levels: int | None = None,
) -> str:
    """Create a new trading strategy.

    Args:
        strategy_type: One of "trailing-stop", "bracket", "scale-out", "grid", "pullback-trailing".
        symbol: Stock ticker (e.g. "AAPL").
        qty: Number of shares per trade.
        trailing_pct: Trailing stop percentage (for trailing-stop and pullback-trailing).
        pullback_pct: Pullback % from high to trigger buy (for pullback-trailing, default 5).
        take_profit: Take profit percentage (for bracket strategy).
        stop_loss: Stop loss percentage (for bracket strategy).
        entry_price: Limit entry price. If omitted, uses market order.
        levels: Number of grid levels (for grid strategy).
    """
    from trader.app.strategies import create_strategy as _create_strategy
    from trader.schemas.strategies import StrategyCreate

    try:
        request = StrategyCreate(
            strategy_type=strategy_type,
            symbol=symbol.upper(),
            qty=qty,
            trailing_pct=trailing_pct,
            pullback_pct=pullback_pct,
            take_profit=take_profit,
            stop_loss=stop_loss,
            entry_price=entry_price,
            levels=levels,
        )
        return _ok(_create_strategy(_config(), request))
    except AppError as e:
        return _err(e)


def remove_strategy(strategy_id: str) -> str:
    """Delete a strategy by ID.

    Args:
        strategy_id: The strategy ID to remove.
    """
    from trader.app.strategies import remove_strategy as _remove_strategy

    try:
        return _ok(_remove_strategy(strategy_id))
    except AppError as e:
        return _err(e)


def pause_strategy(strategy_id: str) -> str:
    """Pause an active strategy.

    Args:
        strategy_id: The strategy ID to pause.
    """
    from trader.app.strategies import pause_strategy as _pause_strategy

    try:
        return _ok(_pause_strategy(strategy_id))
    except AppError as e:
        return _err(e)


def resume_strategy(strategy_id: str) -> str:
    """Resume a paused strategy.

    Args:
        strategy_id: The strategy ID to resume.
    """
    from trader.app.strategies import resume_strategy as _resume_strategy

    try:
        return _ok(_resume_strategy(strategy_id))
    except AppError as e:
        return _err(e)


def set_strategy_enabled(strategy_id: str, enabled: bool) -> str:
    """Enable or disable a strategy.

    Args:
        strategy_id: The strategy ID.
        enabled: True to enable, False to disable.
    """
    from trader.app.strategies import set_strategy_enabled as _set_enabled

    try:
        return _ok(_set_enabled(strategy_id, enabled))
    except AppError as e:
        return _err(e)


def schedule_strategy(strategy_id: str, schedule_at: str) -> str:
    """Schedule a strategy to start at a specific time.

    The strategy will be disabled until the schedule time arrives.
    Once the time arrives, the engine will automatically enable it.

    Args:
        strategy_id: The strategy ID to schedule.
        schedule_at: ISO datetime string (e.g., "2026-02-13T09:30:00").
    """
    from datetime import datetime
    from trader.app.strategies import schedule_strategy as _schedule_strategy

    try:
        # Parse ISO datetime string
        schedule_dt = datetime.fromisoformat(schedule_at)
        return _ok(_schedule_strategy(strategy_id, schedule_dt))
    except ValueError as e:
        return _err(
            ValidationError(
                message=f"Invalid datetime format: {schedule_at}. Use ISO format: '2026-02-13T09:30:00'",
                code="INVALID_DATETIME_FORMAT",
            )
        )
    except AppError as e:
        return _err(e)


def cancel_schedule(strategy_id: str) -> str:
    """Cancel a scheduled strategy.

    This clears the schedule and leaves the strategy in its current state.

    Args:
        strategy_id: The strategy ID to cancel schedule for.
    """
    from trader.app.strategies import cancel_schedule as _cancel_schedule

    try:
        return _ok(_cancel_schedule(strategy_id))
    except AppError as e:
        return _err(e)


def list_scheduled_strategies() -> str:
    """List all strategies with active schedules.

    Returns a list of strategies that are scheduled to start at a future time.
    """
    from trader.app.strategies import list_scheduled_strategies as _list_scheduled

    try:
        return _ok(_list_scheduled())
    except AppError as e:
        return _err(e)


# =============================================================================
# Backtest Tools
# =============================================================================


def run_backtest(
    strategy_type: str,
    symbol: str,
    start: str,
    end: str,
    qty: int = 10,
    trailing_pct: float | None = None,
    take_profit: float | None = None,
    stop_loss: float | None = None,
    data_source: str = "csv",
    initial_capital: float = 100000.0,
    save: bool = True,
) -> str:
    """Run a backtest on historical data.

    Subject to MCP rate limits and timeout (see MCP_BACKTEST_TIMEOUT_SECONDS).

    Args:
        strategy_type: "trailing-stop" or "bracket".
        symbol: Stock ticker (e.g. "AAPL").
        start: Start date (YYYY-MM-DD).
        end: End date (YYYY-MM-DD).
        qty: Shares per trade.
        trailing_pct: Trailing stop percentage (trailing-stop strategy).
        take_profit: Take profit percentage (bracket strategy).
        stop_loss: Stop loss percentage (bracket strategy).
        data_source: "csv" or "alpaca".
        initial_capital: Starting capital for simulation.
        save: Whether to save results to disk.
    """
    from trader.app.backtests import run_backtest as _run_backtest
    from trader.mcp.limits import (
        check_rate_limit,
        get_backtest_timeout_seconds,
        run_with_timeout,
    )
    from trader.schemas.backtests import BacktestRequest

    try:
        check_rate_limit("long_running")
        request = BacktestRequest(
            strategy_type=strategy_type,
            symbol=symbol.upper(),
            start=start,
            end=end,
            qty=qty,
            trailing_pct=trailing_pct,
            take_profit=take_profit,
            stop_loss=stop_loss,
            data_source=data_source,
            initial_capital=initial_capital,
            save=save,
        )
        timeout = get_backtest_timeout_seconds()
        result = run_with_timeout(
            lambda: _run_backtest(_config(), request),
            timeout_seconds=timeout,
            task_name="run_backtest",
        )
        return _ok(result)
    except AppError as e:
        return _err(e)


def list_backtests() -> str:
    """List all saved backtest results."""
    from trader.app.backtests import list_backtests_app

    try:
        result = list_backtests_app()
        return json.dumps(
            [b.model_dump() for b in result], indent=2, default=str
        )
    except AppError as e:
        return _err(e)


def show_backtest(backtest_id: str) -> str:
    """Get full results for a specific backtest.

    Args:
        backtest_id: The backtest ID.
    """
    from trader.app.backtests import show_backtest as _show_backtest

    try:
        return _ok(_show_backtest(backtest_id))
    except AppError as e:
        return _err(e)


def compare_backtests(backtest_ids: list[str]) -> str:
    """Compare multiple backtests side by side.

    Args:
        backtest_ids: List of backtest IDs to compare.
    """
    from trader.app.backtests import compare_backtests as _compare

    try:
        results = _compare(backtest_ids)
        return json.dumps(
            [r.model_dump() for r in results], indent=2, default=str
        )
    except AppError as e:
        return _err(e)


def delete_backtest(backtest_id: str) -> str:
    """Delete a saved backtest result.

    Args:
        backtest_id: The backtest ID to delete.
    """
    from trader.app.backtests import delete_backtest_app

    try:
        return _ok(delete_backtest_app(backtest_id))
    except AppError as e:
        return _err(e)


# =============================================================================
# Analysis Tools
# =============================================================================


def analyze_performance(
    symbol: str | None = None,
    days: int = 30,
    limit: int = 1000,
) -> str:
    """Analyze realized trade performance (win rate, profit factor, etc.).

    Args:
        symbol: Filter by ticker. If omitted, analyzes all trades.
        days: Number of days to look back.
        limit: Maximum number of trades to analyze.
    """
    from trader.app.analysis import analyze_trade_performance

    try:
        result = analyze_trade_performance(
            symbol=symbol.upper() if symbol else None,
            days=days,
            limit=limit,
        )
        if result is None:
            return json.dumps({"message": "No trades found for analysis."})
        return _ok(result)
    except AppError as e:
        return _err(e)


def get_trade_history(symbol: str | None = None, limit: int = 20) -> str:
    """Get recent trade records.

    Args:
        symbol: Filter by ticker. If omitted, returns all symbols.
        limit: Maximum number of trades to return.
    """
    from trader.app.analysis import get_trade_history as _get_history

    try:
        result = _get_history(
            symbol=symbol.upper() if symbol else None, limit=limit
        )
        return json.dumps(result, indent=2, default=str)
    except AppError as e:
        return _err(e)


def get_today_pnl() -> str:
    """Get today's realized profit/loss."""
    from trader.app.analysis import get_today_pnl as _get_today_pnl

    try:
        pnl = _get_today_pnl()
        return json.dumps({"today_pnl": str(pnl)}, indent=2)
    except AppError as e:
        return _err(e)


# =============================================================================
# Indicator Tools
# =============================================================================


def list_indicators() -> str:
    """List all available technical indicators (SMA, RSI, MACD, etc.)."""
    from trader.app.indicators import list_all_indicators

    try:
        result = list_all_indicators()
        return json.dumps(
            [i.model_dump() for i in result], indent=2, default=str
        )
    except AppError as e:
        return _err(e)


def describe_indicator(name: str) -> str:
    """Get detailed information about a specific technical indicator.

    Args:
        name: Indicator name (e.g. "sma", "rsi", "macd").
    """
    from trader.app.indicators import describe_indicator as _describe

    try:
        return _ok(_describe(name.lower()))
    except AppError as e:
        return _err(e)


# =============================================================================
# Optimization Tools
# =============================================================================


def run_optimization(
    strategy_type: str,
    symbol: str,
    start: str,
    end: str,
    params: dict[str, list[Any]],
    objective: str = "total_return_pct",
    method: str = "grid",
    num_samples: int | None = None,
    data_source: str = "csv",
    initial_capital: float = 100000.0,
    save: bool = True,
) -> str:
    """Run parameter optimization over a grid of strategy parameters.

    Subject to MCP rate limits and timeout (see MCP_OPTIMIZATION_TIMEOUT_SECONDS).

    Args:
        strategy_type: "trailing-stop" or "bracket".
        symbol: Stock ticker (e.g. "AAPL").
        start: Start date (YYYY-MM-DD).
        end: End date (YYYY-MM-DD).
        params: Parameter grid, e.g. {"trailing_pct": [0.02, 0.03, 0.05]}.
        objective: Metric to optimize ("total_return_pct", "sharpe_ratio", "win_rate", etc.).
        method: "grid" for exhaustive search or "random" for sampling.
        num_samples: Number of random samples (only for method="random").
        data_source: "csv" or "alpaca".
        initial_capital: Starting capital for simulation.
        save: Whether to save results to disk.
    """
    from trader.app.optimization import run_optimization as _run_opt
    from trader.mcp.limits import (
        check_rate_limit,
        get_optimization_timeout_seconds,
        run_with_timeout,
    )
    from trader.schemas.optimization import OptimizeRequest

    try:
        check_rate_limit("long_running")
        request = OptimizeRequest(
            strategy_type=strategy_type,
            symbol=symbol.upper(),
            start=start,
            end=end,
            params=params,
            objective=objective,
            method=method,
            num_samples=num_samples,
            data_source=data_source,
            initial_capital=initial_capital,
            save=save,
        )
        timeout = get_optimization_timeout_seconds()
        result = run_with_timeout(
            lambda: _run_opt(_config(), request),
            timeout_seconds=timeout,
            task_name="run_optimization",
        )
        return _ok(result)
    except AppError as e:
        return _err(e)


# =============================================================================
# Safety Tools
# =============================================================================


def get_safety_status() -> str:
    """Get current safety check status and limits.

    Returns position size limits, daily loss limits, and trade count limits.
    """
    from trader.app.data import get_safety_status as _get_safety

    try:
        return _ok(_get_safety(_config()))
    except AppError as e:
        return _err(e)


# =============================================================================
# Tool Registration
# =============================================================================


def _with_mcp_audit(fn: Any) -> Any:
    """Wrap a tool so audit source is set to 'mcp' for the duration of the call."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from trader.audit import set_audit_source

        set_audit_source("mcp")
        return fn(*args, **kwargs)

    return wrapper


_ALL_TOOLS = [
    # Engine
    get_status,
    stop_engine,
    # Portfolio & Market Data
    get_balance,
    get_positions,
    get_portfolio,
    get_quote,
    get_top_movers,
    # Orders
    place_order,
    list_orders,
    cancel_order,
    # Strategies
    list_strategies,
    get_strategy,
    create_strategy,
    remove_strategy,
    pause_strategy,
    resume_strategy,
    set_strategy_enabled,
    schedule_strategy,
    cancel_schedule,
    list_scheduled_strategies,
    # Backtests
    run_backtest,
    list_backtests,
    show_backtest,
    compare_backtests,
    delete_backtest,
    # Analysis
    analyze_performance,
    get_trade_history,
    get_today_pnl,
    # Indicators
    list_indicators,
    describe_indicator,
    # Optimization
    run_optimization,
    # Safety
    get_safety_status,
]


def register_tools(server: FastMCP) -> None:
    """Register all MCP tools on the provided server."""
    for tool_fn in _ALL_TOOLS:
        server.tool()(_with_mcp_audit(tool_fn))  # type: ignore[arg-type]


# =============================================================================
# Server Setup
# =============================================================================


def build_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
) -> FastMCP:
    """Create a FastMCP server with configured host/port."""
    server = FastMCP("autotrader", host=host, port=port, log_level=log_level)
    register_tools(server)
    return server


mcp = build_server()


async def run_server(
    transport: Literal["stdio", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    mount_path: str | None = None,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    ssl_certfile: str | None = None,
    ssl_keyfile: str | None = None,
) -> None:
    """Run the MCP server with the selected transport (stdio or streamable HTTP)."""
    import sys
    import traceback

    try:
        print(f"Building MCP server (transport={transport})...", file=sys.stderr)
        server = build_server(host=host, port=port, log_level=log_level)
        print(f"Server built successfully", file=sys.stderr)

        if transport == "stdio":
            print(f"Starting stdio transport...", file=sys.stderr)
            await server.run_stdio_async()
            return

        if transport == "streamable-http":
            import uvicorn

            if ssl_certfile or ssl_keyfile:
                if not ssl_certfile or not ssl_keyfile:
                    raise ValueError("Both --ssl-certfile and --ssl-keyfile are required for HTTPS")
                app = server.streamable_http_app()
                config = uvicorn.Config(
                    app,
                    host=host,
                    port=port,
                    log_level=log_level.lower(),
                    ssl_certfile=ssl_certfile,
                    ssl_keyfile=ssl_keyfile,
                )
            else:
                app = server.streamable_http_app()
                config = uvicorn.Config(app, host=host, port=port, log_level=log_level.lower())
            print(f"Starting streamable HTTP at {'https' if ssl_certfile else 'http'}://{host}:{port}...", file=sys.stderr)
            uvicorn_server = uvicorn.Server(config)
            await uvicorn_server.serve()
            return
    except Exception as e:
        print(f"MCP server startup error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise
