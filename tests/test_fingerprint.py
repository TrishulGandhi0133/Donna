"""Tests for donna.system.fingerprint — system discovery module."""

from __future__ import annotations

from unittest.mock import patch

from donna.system.fingerprint import SystemFingerprint, _probe_tool


class TestProbing:
    """Verify tool detection probes."""

    def test_probe_python_version(self) -> None:
        """Python should always be detected."""
        import sys
        result = _probe_tool([sys.executable, "--version"])
        assert result is not None
        assert "Python" in result or "python" in result

    def test_probe_nonexistent_tool(self) -> None:
        """A nonexistent tool should return None."""
        result = _probe_tool(["this_tool_does_not_exist_12345", "--version"])
        assert result is None


class TestSystemFingerprint:
    """Verify the full system fingerprint."""

    def test_detect_returns_fingerprint(self) -> None:
        fp = SystemFingerprint.detect()
        assert fp.os_name != ""
        assert fp.username != ""
        assert fp.home_dir != ""
        assert fp.cwd != ""

    def test_python_always_installed(self) -> None:
        fp = SystemFingerprint.detect()
        assert "Python" in fp.installed_tools

    def test_to_prompt_section_format(self) -> None:
        fp = SystemFingerprint.detect()
        section = fp.to_prompt_section()
        assert "## System Environment" in section
        assert "OS:" in section
        assert "User:" in section
        assert "Installed Tools" in section
        assert "✅ Python" in section

    def test_missing_tools_shown(self) -> None:
        """If a tool is missing, it should appear in the NOT Installed section."""
        fp = SystemFingerprint()
        fp.os_name = "TestOS"
        fp.missing_tools = ["FakeTool"]
        section = fp.to_prompt_section()
        assert "NOT Installed" in section
        assert "❌ FakeTool" in section

    def test_fingerprint_caching(self) -> None:
        """get_fingerprint should return the same object (cached)."""
        from donna.system.fingerprint import get_fingerprint
        fp1 = get_fingerprint()
        fp2 = get_fingerprint()
        assert fp1 is fp2
