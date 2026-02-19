"""Tests for donna.tools — registry, decorators, and built-in tools."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from donna.tools.registry import (
    ToolEntry,
    get_all_tools,
    get_tool,
    get_tool_schemas,
    register_function,
)
# This import triggers auto-registration of all built-in tools
import donna.tools  # noqa: F401
from donna.tools.filesystem import read_file, list_dir, write_file, delete_file
from donna.tools.shell_exec import execute_shell
from donna.tools.clipboard import read_clipboard, write_clipboard
from donna.tools.process import launch_app


class TestToolRegistry:
    """Verify the @tool decorator and registry operations."""

    def test_builtin_tools_registered(self) -> None:
        """All built-in tools should be auto-registered on import."""
        all_tools = get_all_tools()
        expected = {
            "read_file", "list_dir", "write_file", "delete_file",
            "execute_shell",
            "read_clipboard", "write_clipboard",
            "launch_app", "kill_process",
        }
        assert expected.issubset(set(all_tools.keys())), (
            f"Missing tools: {expected - set(all_tools.keys())}"
        )

    def test_get_tool_returns_entry(self) -> None:
        entry = get_tool("read_file")
        assert entry is not None
        assert isinstance(entry, ToolEntry)
        assert entry.name == "read_file"
        assert entry.safety == "green"

    def test_get_tool_missing_returns_none(self) -> None:
        assert get_tool("nonexistent_tool") is None

    def test_tool_schema_has_parameters(self) -> None:
        entry = get_tool("read_file")
        assert entry is not None
        schema = entry.schema
        assert schema.name == "read_file"
        assert "properties" in schema.parameters
        assert "path" in schema.parameters["properties"]

    def test_tool_schemas_filtering(self) -> None:
        schemas = get_tool_schemas(["read_file", "list_dir"])
        assert len(schemas) == 2
        names = {s.name for s in schemas}
        assert names == {"read_file", "list_dir"}

    def test_safety_classification(self) -> None:
        """Green tools should be green, red tools should be red."""
        green_tools = ["read_file", "list_dir", "read_clipboard", "write_clipboard", "launch_app"]
        red_tools = ["write_file", "delete_file", "kill_process"]

        for name in green_tools:
            entry = get_tool(name)
            assert entry is not None and entry.safety == "green", f"{name} should be green"

        for name in red_tools:
            entry = get_tool(name)
            assert entry is not None and entry.safety == "red", f"{name} should be red"

        # execute_shell is green in registry but dynamically classified
        entry = get_tool("execute_shell")
        assert entry is not None and entry.safety == "green"

    def test_register_function_dynamic(self) -> None:
        """register_function should add a tool at runtime."""
        def my_skill(x: str) -> str:
            return x.upper()

        register_function(my_skill, name="_test_dynamic_skill", description="Uppercases input")
        entry = get_tool("_test_dynamic_skill")
        assert entry is not None
        assert entry.func("hello") == "HELLO"


class TestFilesystemTools:
    """Test file system tools against real temp files."""

    def test_read_file_existing(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello donna")
            f.flush()
            result = read_file(f.name)
        assert "hello donna" in result
        os.unlink(f.name)

    def test_read_file_missing(self) -> None:
        result = read_file("/nonexistent/path/file.txt")
        assert "[ERROR]" in result

    def test_list_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "test.txt").write_text("x")
            (Path(td) / "subdir").mkdir()
            result = list_dir(td)
        assert "[FILE]" in result
        assert "[DIR]" in result
        assert "test.txt" in result

    def test_write_and_delete_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = str(Path(td) / "output.txt")
            result = write_file(target, "written by donna")
            assert "[OK]" in result
            assert Path(target).read_text() == "written by donna"

            result = delete_file(target)
            assert "[OK]" in result
            assert not Path(target).exists()

    def test_delete_missing_file(self) -> None:
        result = delete_file("/nonexistent/file.txt")
        assert "[ERROR]" in result


class TestShellExecTool:
    """Test shell command execution."""

    def test_echo_command(self) -> None:
        result = execute_shell("echo 'hello donna'")
        assert "hello donna" in result
        assert "[EXIT CODE:" in result

    def test_failing_command(self) -> None:
        """A command that exits non-zero should report a non-zero exit code."""
        result = execute_shell("python -c \"import sys; sys.exit(42)\"")
        assert "[EXIT CODE:" in result
        # On PowerShell, exit codes from python -c may differ, but it shouldn't be 0
        assert "[EXIT CODE: 0]" not in result

    def test_cwd_parameter(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            result = execute_shell("echo working", cwd=td)
        assert "working" in result

    def test_safe_command_detection(self) -> None:
        """Safe commands should be auto-detected."""
        from donna.tools.shell_exec import _is_safe_command
        assert _is_safe_command("systeminfo")
        assert _is_safe_command("echo hello")
        assert _is_safe_command("git status")
        assert _is_safe_command("Get-Date")
        assert not _is_safe_command("pip install flask")
        assert not _is_safe_command("rm -rf /")
