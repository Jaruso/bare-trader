"""Tests for Pydantic schema models."""

from datetime import datetime
from decimal import Decimal

from trader.errors import AppError
from trader.schemas.analysis import (
    OpenPositionSchema,
    TradeStatsSchema,
)
from trader.schemas.backtests import (
    BacktestRequest,
    BacktestSummary,
)
from trader.schemas.common import DateRange, PaginationParams
from trader.schemas.engine import EngineStatus
from trader.schemas.errors import ErrorResponse
from trader.schemas.indicators import IndicatorInfo
from trader.schemas.orders import OrderRequest, OrderResponse
from trader.schemas.portfolio import (
    AccountInfo,
    BalanceResponse,
    PositionInfo,
    QuoteResponse,
)
from trader.schemas.strategies import (
    StrategyCreate,
    StrategyListResponse,
)


class TestCommonSchemas:
    """Test common shared schemas."""

    def test_date_range(self) -> None:
        dr = DateRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 12, 31),
        )
        assert dr.start.year == 2024
        assert dr.end.month == 12

    def test_pagination_params_defaults(self) -> None:
        p = PaginationParams()
        assert p.limit == 100
        assert p.offset == 0

    def test_pagination_params_custom(self) -> None:
        p = PaginationParams(limit=10, offset=5)
        assert p.limit == 10
        assert p.offset == 5


class TestErrorResponse:
    """Test error response schema."""

    def test_from_error(self) -> None:
        err = AppError(
            message="something broke",
            code="TEST_ERROR",
            details={"key": "val"},
            suggestion="retry",
        )
        resp = ErrorResponse.from_error(err)
        assert resp.error == "TEST_ERROR"
        assert resp.message == "something broke"
        assert resp.details == {"key": "val"}
        assert resp.suggestion == "retry"

    def test_from_error_minimal(self) -> None:
        err = AppError("simple error", code="APP_ERROR")
        resp = ErrorResponse.from_error(err)
        assert resp.error == "APP_ERROR"
        assert resp.message == "simple error"
        # details is {} when no details provided
        assert resp.details == {}
        assert resp.suggestion is None


class TestAccountInfo:
    """Test AccountInfo schema."""

    def test_creation(self) -> None:
        acct = AccountInfo(
            cash=Decimal("50000"),
            buying_power=Decimal("100000"),
            equity=Decimal("75000"),
            portfolio_value=Decimal("75000"),
        )
        assert acct.cash == Decimal("50000")
        assert acct.currency == "USD"
        assert acct.daytrade_count == 0
        assert acct.pattern_day_trader is False

    def test_from_domain(self) -> None:
        """Test from_domain works with broker Account."""
        from trader.api.broker import Account

        domain = Account(
            cash=Decimal("10000"),
            buying_power=Decimal("20000"),
            equity=Decimal("15000"),
            portfolio_value=Decimal("15000"),
            currency="USD",
            daytrade_count=2,
        )
        schema = AccountInfo.from_domain(domain)
        assert schema.cash == domain.cash
        assert schema.buying_power == domain.buying_power
        assert schema.equity == domain.equity
        assert schema.daytrade_count == 2


class TestPositionInfo:
    """Test PositionInfo schema."""

    def test_from_domain(self) -> None:
        from trader.api.broker import Position

        pos = Position(
            symbol="AAPL",
            qty=Decimal("10"),
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            market_value=Decimal("1600.00"),
            unrealized_pl=Decimal("100.00"),
            unrealized_pl_pct=Decimal("6.67"),
        )
        schema = PositionInfo.from_domain(pos)
        assert schema.symbol == "AAPL"
        assert schema.qty == Decimal("10")
        assert schema.market_value == Decimal("1600.00")


class TestQuoteResponse:
    """Test QuoteResponse schema."""

    def test_from_domain(self) -> None:
        from trader.api.broker import Quote

        q = Quote(
            symbol="AAPL",
            bid=Decimal("149.50"),
            ask=Decimal("150.00"),
            last=Decimal("149.75"),
            volume=1000000,
        )
        schema = QuoteResponse.from_domain(q)
        assert schema.symbol == "AAPL"
        assert schema.spread == Decimal("0.50")


class TestBalanceResponse:
    """Test BalanceResponse schema."""

    def test_creation(self) -> None:
        acct = AccountInfo(
            cash=Decimal("50000"),
            buying_power=Decimal("100000"),
            equity=Decimal("75000"),
            portfolio_value=Decimal("75000"),
        )
        bal = BalanceResponse(
            account=acct,
            positions=[],
            market_open=True,
            total_positions_value=Decimal("0"),
            total_unrealized_pl=Decimal("0"),
        )
        assert bal.market_open is True
        assert bal.day_change is None
        assert len(bal.positions) == 0


class TestOrderSchemas:
    """Test order request/response schemas."""

    def test_order_request(self) -> None:
        req = OrderRequest(
            symbol="AAPL",
            qty=10,
            price=Decimal("150.00"),
            side="buy",
        )
        assert req.symbol == "AAPL"
        assert req.qty == 10
        assert req.side == "buy"

    def test_order_request_sell(self) -> None:
        req = OrderRequest(
            symbol="MSFT",
            qty=5,
            price=Decimal("300.00"),
            side="sell",
        )
        assert req.side == "sell"

    def test_order_response_from_domain(self) -> None:
        from trader.api.broker import (
            Order,
            OrderSide,
            OrderStatus,
            OrderType,
        )

        order = Order(
            id="ord-123",
            symbol="AAPL",
            side=OrderSide.BUY,
            qty=Decimal("10"),
            order_type=OrderType.LIMIT,
            status=OrderStatus.FILLED,
            filled_qty=Decimal("10"),
            filled_avg_price=Decimal("150.00"),
        )
        schema = OrderResponse.from_domain(order)
        assert schema.id == "ord-123"
        assert schema.symbol == "AAPL"
        assert schema.side == "buy"
        assert schema.status == "filled"


class TestStrategySchemas:
    """Test strategy schemas."""

    def test_strategy_create(self) -> None:
        sc = StrategyCreate(
            strategy_type="trailing-stop",
            symbol="AAPL",
            qty=10,
            trailing_pct=Decimal("2.5"),
        )
        assert sc.strategy_type == "trailing-stop"
        assert sc.symbol == "AAPL"

    def test_strategy_list_response(self) -> None:
        resp = StrategyListResponse(strategies=[], count=0)
        assert resp.count == 0


class TestBacktestSchemas:
    """Test backtest schemas."""

    def test_backtest_request(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbol="AAPL",
            start="2024-01-01",
            end="2024-06-30",
            qty=10,
            trailing_pct=2.0,
        )
        assert req.strategy_type == "trailing-stop"
        assert req.save is True  # default
        assert req.initial_capital == 100000.0

    def test_backtest_summary(self) -> None:
        summary = BacktestSummary(
            id="bt-123",
            strategy_type="trailing-stop",
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-06-30",
            total_return_pct=Decimal("12.5"),
            win_rate=Decimal("60.0"),
            total_trades=25,
            max_drawdown_pct=Decimal("5.0"),
            created_at="2024-07-01T00:00:00",
        )
        assert summary.id == "bt-123"
        assert summary.total_return_pct == Decimal("12.5")


class TestAnalysisSchemas:
    """Test analysis schemas."""

    def test_trade_stats_schema(self) -> None:
        stats = TradeStatsSchema(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=Decimal("60.0"),
            gross_profit=Decimal("800.00"),
            gross_loss=Decimal("300.00"),
            net_profit=Decimal("500.00"),
            profit_factor=Decimal("2.67"),
            avg_win=Decimal("133.33"),
            avg_loss=Decimal("75.00"),
            largest_win=Decimal("250.00"),
            largest_loss=Decimal("100.00"),
            avg_hold_minutes=Decimal("45.5"),
        )
        assert stats.win_rate == Decimal("60.0")
        assert stats.total_trades == 10

    def test_open_position_schema(self) -> None:
        pos = OpenPositionSchema(
            symbol="AAPL",
            lots=2,
            quantity=Decimal("10"),
            avg_cost=Decimal("150.00"),
        )
        assert pos.symbol == "AAPL"
        assert pos.lots == 2


class TestIndicatorInfo:
    """Test indicator info schema."""

    def test_creation(self) -> None:
        ind = IndicatorInfo(
            name="SMA",
            description="Simple Moving Average",
            params={"period": "20"},
            output="sma_20",
        )
        assert ind.name == "SMA"
        assert ind.output == "sma_20"

    def test_from_domain(self) -> None:
        from trader.indicators.base import IndicatorSpec

        spec = IndicatorSpec(
            name="RSI",
            description="Relative Strength Index",
            params={"period": "14"},
            output="rsi",
        )
        schema = IndicatorInfo.from_domain(spec)
        assert schema.name == "RSI"
        assert schema.description == "Relative Strength Index"


class TestEngineStatus:
    """Test engine status schema."""

    def test_not_running(self) -> None:
        status = EngineStatus(
            running=False,
            environment="paper",
            service="alpaca",
            base_url="https://paper-api.alpaca.markets",
            api_key_configured=True,
        )
        assert status.running is False
        assert status.pid is None

    def test_running(self) -> None:
        status = EngineStatus(
            running=True,
            pid=12345,
            environment="paper",
            service="alpaca",
            base_url="https://paper-api.alpaca.markets",
            api_key_configured=True,
        )
        assert status.running is True
        assert status.pid == 12345


class TestJsonSerialization:
    """Test that schemas serialize to JSON correctly."""

    def test_account_info_json(self) -> None:
        acct = AccountInfo(
            cash=Decimal("50000"),
            buying_power=Decimal("100000"),
            equity=Decimal("75000"),
            portfolio_value=Decimal("75000"),
        )
        data = acct.model_dump()
        assert isinstance(data, dict)
        assert "cash" in data
        assert "equity" in data

    def test_error_response_json(self) -> None:
        resp = ErrorResponse(
            error="TEST",
            message="test error",
        )
        data = resp.model_dump()
        assert data["error"] == "TEST"
        assert data["message"] == "test error"
