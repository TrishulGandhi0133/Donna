"""Tests for donna.cli — Typer CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from donna.cli import app

runner = CliRunner()


class TestCLI:
    """Test the Typer sub-commands."""

    def test_version_flag(self) -> None:
        """donna --version should print the version and exit 0."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "donna" in result.output.lower()

    def test_info_command(self) -> None:
        """donna info should print config summary without errors."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        # Should mention the model name
        assert "Model" in result.output or "model" in result.output

    def test_run_command_accepts_prompt(self) -> None:
        """donna run should accept a prompt (may fail if no LLM is running, but shouldn't crash)."""
        result = runner.invoke(app, ["run", "hello world"])
        # The command may fail if no LLM backend is available, but it should not crash
        assert result.exit_code in (0, 1)

    def test_setup_command_exists(self) -> None:
        """donna setup should be a valid command."""
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0
        assert "setup" in result.output.lower() or "wizard" in result.output.lower()

    def test_no_args_shows_help(self) -> None:
        """donna (no args) should show help text."""
        result = runner.invoke(app, [])
        # Typer/Click may return 0 or 2 when displaying help
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output or "usage" in result.output.lower()
