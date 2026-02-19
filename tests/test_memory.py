"""Tests for donna.memory.feedback — the Grudge memory system."""

from __future__ import annotations

import pytest

from donna.memory.feedback import append_feedback, read_feedback, clear_feedback


@pytest.fixture(autouse=True)
def _clean_test_agent_feedback():
    """Ensure test agent feedback is clean before and after each test."""
    clear_feedback("_test_agent")
    yield
    clear_feedback("_test_agent")


class TestFeedback:
    """Test the feedback read/write/clear cycle."""

    def test_read_empty_returns_empty_string(self) -> None:
        """Reading feedback for an agent with no file should return ''."""
        assert read_feedback("_test_agent") == ""

    def test_append_and_read(self) -> None:
        """Appending feedback should be readable back."""
        append_feedback("_test_agent", "use poetry not pip")
        content = read_feedback("_test_agent")
        assert "use poetry not pip" in content

    def test_append_multiple(self) -> None:
        """Multiple appends should all appear in the file."""
        append_feedback("_test_agent", "first correction")
        append_feedback("_test_agent", "second correction")
        content = read_feedback("_test_agent")
        assert "first correction" in content
        assert "second correction" in content

    def test_entries_are_timestamped(self) -> None:
        """Each entry should contain a UTC timestamp."""
        append_feedback("_test_agent", "timestamped entry")
        content = read_feedback("_test_agent")
        assert "UTC" in content

    def test_clear_removes_feedback(self) -> None:
        """clear_feedback should remove all entries."""
        append_feedback("_test_agent", "will be deleted")
        clear_feedback("_test_agent")
        assert read_feedback("_test_agent") == ""
