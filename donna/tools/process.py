"""
donna.tools.process — Process and application management tools.

Gives the LLM the ability to launch applications and kill running
processes.  ``launch_app`` is **green** (opening an app is safe);
``kill_process`` is **red** (terminating a process can lose data).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys

from donna.tools.registry import tool


@tool(
    name="launch_app",
    safety="green",
    description="Launch an application or open a file with the default handler.",
)
def launch_app(target: str) -> str:
    """Open *target* using the OS default handler.

    Works for:
    - Applications: ``"code"`` (VS Code), ``"notepad"``
    - Files: ``"report.pdf"`` → opens in default PDF viewer
    - URLs: ``"https://example.com"`` → opens in default browser

    Parameters
    ----------
    target : str
        Application name, file path, or URL to open.
    """
    try:
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
        return f"[OK] Launched: {target}"
    except Exception as exc:
        return f"[ERROR] Failed to launch '{target}': {exc}"


@tool(
    name="kill_process",
    safety="red",
    description="Kill a running process by its PID.",
)
def kill_process(pid: int) -> str:
    """Terminate the process with the given *pid*.

    ⚠️  This is a **red** tool — killing a process may lose unsaved work.

    Parameters
    ----------
    pid : int
        The process ID to terminate.
    """
    try:
        os.kill(pid, signal.SIGTERM)
        return f"[OK] Sent SIGTERM to PID {pid}."
    except ProcessLookupError:
        return f"[ERROR] No process found with PID {pid}."
    except PermissionError:
        return f"[ERROR] Permission denied to kill PID {pid}."
    except Exception as exc:
        return f"[ERROR] {type(exc).__name__}: {exc}"
