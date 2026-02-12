"""Tests for the central audit log (Phase 3)."""

from pathlib import Path

from trader.audit import get_audit_source, log_action, set_audit_source


def test_set_and_get_audit_source() -> None:
    set_audit_source("cli")
    assert get_audit_source() == "cli"
    set_audit_source("mcp")
    assert get_audit_source() == "mcp"


def test_log_action_no_write_when_log_dir_none() -> None:
    """When log_dir is None, log_action does not write or raise."""
    log_action("test_action", {"key": "value"}, log_dir=None)
    # No exception; no file created


def test_log_action_writes_jsonl(tmp_path: Path) -> None:
    """log_action appends one JSON line to audit.log."""
    set_audit_source("cli")
    log_action("place_order", {"symbol": "AAPL", "qty": 10}, log_dir=tmp_path)
    log_file = tmp_path / "audit.log"
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    record = __import__("json").loads(lines[0])
    assert record["source"] == "cli"
    assert record["action"] == "place_order"
    assert record["details"] == {"symbol": "AAPL", "qty": 10}
    assert "ts" in record
    assert "error" not in record


def test_log_action_with_error(tmp_path: Path) -> None:
    """log_action includes error field when provided."""
    set_audit_source("mcp")
    log_action(
        "place_order",
        {"symbol": "TSLA"},
        error="Order placement failed",
        log_dir=tmp_path,
    )
    record = __import__("json").loads((tmp_path / "audit.log").read_text().strip())
    assert record["error"] == "Order placement failed"
    assert record["source"] == "mcp"


def test_log_action_appends(tmp_path: Path) -> None:
    """Multiple log_action calls append to the same file."""
    set_audit_source("cli")
    log_action("action_a", {"x": 1}, log_dir=tmp_path)
    log_action("action_b", {"x": 2}, log_dir=tmp_path)
    lines = (tmp_path / "audit.log").read_text().strip().split("\n")
    assert len(lines) == 2
    assert __import__("json").loads(lines[0])["action"] == "action_a"
    assert __import__("json").loads(lines[1])["action"] == "action_b"


def test_log_action_creates_log_dir(tmp_path: Path) -> None:
    """log_action creates parent directory if needed."""
    log_dir = tmp_path / "nested" / "logs"
    log_action("test", {}, log_dir=log_dir)
    assert (log_dir / "audit.log").exists()
