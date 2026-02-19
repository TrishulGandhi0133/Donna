"""
donna.tools.shell_exec — Shell command execution tool.

Gives the LLM the ability to run arbitrary shell commands via ``subprocess``.
On Windows, commands run through **PowerShell** so `Get-Date`, `Get-Process`,
etc. all work correctly.

The safety interceptor classifies each invocation as green (safe commands
like ``systeminfo``, ``echo``) or red (anything else).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

from donna.tools.registry import tool

# Maximum output length returned to the model (avoid flooding context)
_MAX_OUTPUT_CHARS = 8000

# Commands that are safe to auto-approve (read-only / informational)
_SAFE_COMMAND_PATTERNS = re.compile(
    r"^("
    r"echo\s|"
    r"systeminfo|"
    r"hostname|"
    r"whoami|"
    r"time\s*/t|"
    r"date\s*/t|"
    r"dir\s|dir$|"
    r"type\s|"
    r"where\s|"
    r"ver\s*$|"
    r"set\s+\w|"
    r"python\s+--version|"
    r"python\s+-V|"
    r"pip\s+(list|show|freeze)|"
    r"node\s+--version|"
    r"git\s+(status|log|branch|diff|show)|"
    r"Get-Date|"
    r"Get-Process|"
    r"Get-ChildItem|"
    r"Get-ComputerInfo|"
    r"Get-Host|"
    r"\$env:\w+"
    r")",
    re.IGNORECASE,
)


def _is_safe_command(command: str) -> bool:
    """Check if a command is read-only / informational."""
    return bool(_SAFE_COMMAND_PATTERNS.match(command.strip()))


@tool(
    name="execute_shell",
    safety="green",  # Safety is handled dynamically by the interceptor
    description="Execute a shell command and return its output.",
)
def execute_shell(command: str, cwd: str = ".") -> str:
    """Run *command* in a subprocess and return stdout + stderr.

    On Windows, runs through PowerShell.  On Linux/macOS, uses the default shell.

    Parameters
    ----------
    command : str
        The shell command to execute (e.g. ``"systeminfo"``).
    cwd : str
        Working directory for the command (defaults to current directory).

    Returns
    -------
    str
        Combined stdout and stderr, truncated to avoid context overflow.
    """
    try:
        # On Windows, use PowerShell so cmdlets like Get-Date work
        if sys.platform == "win32":
            full_cmd = ["powershell", "-NoProfile", "-Command", command]
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=120,
                env=None,
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=120,
                env=None,
            )

        output_parts: list[str] = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[STDERR]\n{result.stderr}")

        output = "\n".join(output_parts) if output_parts else "(no output)"
        exit_code = result.returncode

        # Truncate if too long
        if len(output) > _MAX_OUTPUT_CHARS:
            output = output[:_MAX_OUTPUT_CHARS] + "\n... (output truncated)"

        return f"[EXIT CODE: {exit_code}]\n{output}"

    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out after 120 seconds."
    except FileNotFoundError:
        return f"[ERROR] Shell not found. Platform: {sys.platform}"
    except Exception as exc:
        return f"[ERROR] {type(exc).__name__}: {exc}"
