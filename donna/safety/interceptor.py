"""
donna.safety.interceptor — Red/Green tool-call safety gate.

Before any tool is executed, it passes through this interceptor:

1. Look up the tool's ``safety`` field in the registry.
2. If **green** → execute immediately, return result.
3. If **red** → print a warning, wait for user ``[y/N]``, default deny.

Additionally, even green tools get promoted to red if the arguments
contain dangerous keywords (``rm``, ``sudo``, ``>``).
"""

from __future__ import annotations

import re
from typing import Any

from rich.console import Console
from rich.panel import Panel

from donna.config import get_settings
from donna.models.base import ToolCall
from donna.tools.registry import get_tool, ToolEntry

console = Console()


class SafetyInterceptor:
    """Human-in-the-loop middleware for tool execution.

    Attributes
    ----------
    red_count : int
        Number of red tool calls approved this session.
    max_red : int
        Circuit-breaker — refuse after this many red approvals.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._red_keywords = [kw.lower() for kw in settings.safety.red_keywords]
        # Build a single regex with word boundaries to avoid false positives
        # e.g. "del" should NOT match "models" or "delete" in a path
        escaped = [re.escape(kw) for kw in self._red_keywords]
        self._danger_pattern = re.compile(
            r"(?:^|(?<=\s))(" + "|".join(escaped) + r")(?=\s|$)",
            re.IGNORECASE,
        )
        self._auto_approve_green = settings.safety.auto_approve_green
        self.max_red = settings.safety.max_red_per_session
        self.red_count = 0

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _is_argument_dangerous(self, args: dict[str, Any]) -> bool:
        """Scan tool arguments for dangerous keywords using word boundaries.

        Only matches standalone dangerous words — ``"del"`` will NOT match
        inside ``"models"`` or ``"delete_file"`` path arguments.
        """
        args_str = " ".join(str(v) for v in args.values())
        return bool(self._danger_pattern.search(args_str))

    def classify(self, tool_entry: ToolEntry, tool_call: ToolCall) -> str:
        """Return ``"green"`` or ``"red"`` for a given tool call.

        For ``execute_shell``, uses smart classification:
        - Safe read-only commands (systeminfo, echo, dir) → green
        - Unknown or dangerous commands → red

        For other tools, uses the registry safety field + argument scanning.
        """
        # Special handling for execute_shell — dynamic classification
        if tool_call.name == "execute_shell":
            from donna.tools.shell_exec import _is_safe_command
            command = tool_call.arguments.get("command", "")
            if _is_safe_command(command):
                return "green"
            return "red"

        if tool_entry.safety == "red":
            return "red"
        # Promote green → red if arguments contain dangerous keywords
        if self._is_argument_dangerous(tool_call.arguments):
            return "red"
        return "green"

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, tool_call: ToolCall) -> str:
        """Execute a tool call with safety gating.

        Parameters
        ----------
        tool_call : ToolCall
            The tool invocation requested by the model.

        Returns
        -------
        str
            The tool's output (or an error/denial message).
        """
        entry = get_tool(tool_call.name)
        if entry is None:
            return f"[ERROR] Unknown tool: {tool_call.name}"

        classification = self.classify(entry, tool_call)

        if classification == "green" and self._auto_approve_green:
            return self._run(entry, tool_call)

        # --- Red path: ask user ---
        if self.red_count >= self.max_red:
            return (
                f"[DENIED] Circuit breaker: already approved {self.max_red} "
                f"red actions this session. Refusing '{tool_call.name}'."
            )

        args_display = ", ".join(f"{k}={v!r}" for k, v in tool_call.arguments.items())
        console.print(
            Panel(
                f"[bold]{tool_call.name}[/bold]({args_display})",
                title="[bold red]⚠️  Agent wants to run[/bold red]",
                border_style="red",
            )
        )
        answer = console.input("[bold]Allow? [y/N]: [/bold]").strip().lower()

        if answer in ("y", "yes"):
            self.red_count += 1
            return self._run(entry, tool_call)
        else:
            return f"[DENIED] User refused to allow '{tool_call.name}'."

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _run(entry: ToolEntry, tool_call: ToolCall) -> str:
        """Actually invoke the tool function."""
        try:
            result = entry.func(**tool_call.arguments)
            return str(result)
        except TypeError as exc:
            return f"[ERROR] Bad arguments for '{tool_call.name}': {exc}"
        except Exception as exc:
            return f"[ERROR] Tool '{tool_call.name}' failed: {type(exc).__name__}: {exc}"
