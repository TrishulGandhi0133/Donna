"""
donna.tools.shell_exec — Shell command execution tool.

Gives the LLM the ability to run arbitrary shell commands via ``subprocess``.
This is the most powerful (and dangerous) tool in the toolkit, so it is
always classified as **red** by default.

The safety interceptor will additionally scan the command string for
dangerous keywords (``rm``, ``sudo``, etc.) before prompting for approval.
"""

from __future__ import annotations

import subprocess
import sys

from donna.tools.registry import tool

# Maximum output length returned to the model (avoid flooding context)
_MAX_OUTPUT_CHARS = 8000


@tool(
    name="execute_shell",
    safety="red",
    description="Execute a shell command and return its output.",
)
def execute_shell(command: str, cwd: str = ".") -> str:
    """Run *command* in a subprocess shell and return stdout + stderr.

    Parameters
    ----------
    command : str
        The shell command to execute (e.g. ``"pip install flask"``).
    cwd : str
        Working directory for the command (defaults to current directory).

    Returns
    -------
    str
        Combined stdout and stderr, truncated to avoid context overflow.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=120,
            # Use the user's PATH so tools like git, pip, node work
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
