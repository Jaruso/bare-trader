"""Tests for the shared error hierarchy."""

from trader.errors import (
    AppError,
    BrokerError,
    ConfigurationError,
    EngineError,
    NotFoundError,
    SafetyError,
    ValidationError,
)


class TestAppError:
    """Test base AppError class."""

    def test_basic_creation(self) -> None:
        err = AppError("something went wrong", code="APP_ERROR")
        assert str(err) == "something went wrong"
        assert err.message == "something went wrong"
        assert err.code == "APP_ERROR"
        assert err.details == {}
        assert err.suggestion is None

    def test_with_all_fields(self) -> None:
        err = AppError(
            message="bad input",
            code="CUSTOM_CODE",
            details={"field": "name"},
            suggestion="Try again",
        )
        assert err.message == "bad input"
        assert err.code == "CUSTOM_CODE"
        assert err.details == {"field": "name"}
        assert err.suggestion == "Try again"

    def test_to_dict(self) -> None:
        err = AppError(
            message="test error",
            code="TEST",
            details={"x": 1},
            suggestion="fix it",
        )
        d = err.to_dict()
        assert d["error"] == "TEST"
        assert d["message"] == "test error"
        assert d["details"] == {"x": 1}
        assert d["suggestion"] == "fix it"

    def test_to_dict_minimal(self) -> None:
        err = AppError("minimal", code="APP_ERROR")
        d = err.to_dict()
        assert d["error"] == "APP_ERROR"
        assert d["message"] == "minimal"
        # details is {} by default, so not included in to_dict
        assert "details" not in d
        assert "suggestion" not in d

    def test_is_exception(self) -> None:
        err = AppError("test", code="APP_ERROR")
        assert isinstance(err, Exception)


class TestSubclasses:
    """Test each error subclass has correct defaults."""

    def test_validation_error(self) -> None:
        err = ValidationError(message="invalid qty")
        assert err.code == "VALIDATION_ERROR"
        assert isinstance(err, AppError)

    def test_not_found_error(self) -> None:
        err = NotFoundError(message="no such item")
        assert err.code == "NOT_FOUND"
        assert isinstance(err, AppError)

    def test_configuration_error(self) -> None:
        err = ConfigurationError(message="missing key")
        assert err.code == "CONFIGURATION_ERROR"
        assert isinstance(err, AppError)

    def test_broker_error(self) -> None:
        err = BrokerError(message="connection failed")
        assert err.code == "BROKER_ERROR"
        assert isinstance(err, AppError)

    def test_safety_error(self) -> None:
        err = SafetyError(message="limit exceeded")
        assert err.code == "SAFETY_BLOCKED"
        assert isinstance(err, AppError)

    def test_engine_error(self) -> None:
        err = EngineError(message="engine crashed")
        assert err.code == "ENGINE_ERROR"
        assert isinstance(err, AppError)

    def test_custom_code_override(self) -> None:
        err = ValidationError(
            message="bad field",
            code="INVALID_FIELD",
        )
        assert err.code == "INVALID_FIELD"

    def test_catch_as_app_error(self) -> None:
        """All subclasses should be catchable as AppError."""
        errors = [
            ValidationError("v"),
            NotFoundError("n"),
            ConfigurationError("c"),
            BrokerError("b"),
            SafetyError("s"),
            EngineError("e"),
        ]
        for e in errors:
            try:
                raise e
            except AppError as caught:
                assert caught.message == e.message
