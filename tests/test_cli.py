"""Tests for CLI module."""

from click.testing import CliRunner

from trader.cli.main import cli


def test_cli_help() -> None:
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "BareTrader" in result.output
    assert "status" in result.output


def test_cli_version() -> None:
    """Test CLI version output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_status() -> None:
    """Test status command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "PAPER" in result.output
    assert "alpaca" in result.output


def test_cli_status_prod() -> None:
    """Test status command in prod mode."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--prod", "status"])
    assert result.exit_code == 0
    assert "PROD" in result.output


def test_cli_start_prod_prompts_confirmation() -> None:
    """Test that prod start shows confirmation prompt."""
    runner = CliRunner()
    # Answer 'n' to the confirmation prompt
    result = runner.invoke(cli, ["--prod", "start"], input="n\n")
    assert result.exit_code == 0
    assert "PRODUCTION MODE" in result.output or "not configured" in result.output


def test_cli_strategy_list() -> None:
    """Test strategy list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["strategy", "list"])
    assert result.exit_code == 0
