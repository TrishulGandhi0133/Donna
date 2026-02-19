"""Tests for donna.safety.interceptor — Red/Green safety gate."""

from __future__ import annotations

import donna.tools  # noqa: F401 — registers tools
from donna.models.base import ToolCall
from donna.safety.interceptor import SafetyInterceptor
from donna.tools.registry import get_tool


class TestSafetyClassification:
    """Test how tool calls are classified as green or red."""

    def setup_method(self) -> None:
        self.interceptor = SafetyInterceptor()

    def test_green_tool_classified_green(self) -> None:
        entry = get_tool("read_file")
        assert entry is not None
        tc = ToolCall(id="1", name="read_file", arguments={"path": "test.txt"})
        assert self.interceptor.classify(entry, tc) == "green"

    def test_red_tool_classified_red(self) -> None:
        entry = get_tool("execute_shell")
        assert entry is not None
        tc = ToolCall(id="2", name="execute_shell", arguments={"command": "echo hi"})
        assert self.interceptor.classify(entry, tc) == "red"

    def test_green_tool_promoted_to_red_on_dangerous_args(self) -> None:
        """A green tool should be promoted to red if args contain rm, sudo, etc."""
        entry = get_tool("read_file")
        assert entry is not None
        # Even though read_file is green, the path contains "rm" which triggers promotion
        tc = ToolCall(id="3", name="read_file", arguments={"path": "sudo rm -rf /"})
        assert self.interceptor.classify(entry, tc) == "red"

    def test_unknown_tool_returns_error(self) -> None:
        tc = ToolCall(id="4", name="nonexistent_tool", arguments={})
        result = self.interceptor.execute(tc)
        assert "[ERROR]" in result

    def test_green_tool_auto_executes(self) -> None:
        """A green tool should execute without prompting."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("safety test content")
            f.flush()
            tc = ToolCall(id="5", name="read_file", arguments={"path": f.name})
            result = self.interceptor.execute(tc)
        assert "safety test content" in result
        os.unlink(f.name)


class TestSafetyCircuitBreaker:
    """Test the circuit breaker that limits red approvals per session."""

    def test_circuit_breaker_tracks_count(self) -> None:
        interceptor = SafetyInterceptor()
        assert interceptor.red_count == 0
        assert interceptor.max_red > 0
