"""
donna.agents.base_agent — The ReAct agent loop.

This is the beating heart of Donna.  ``BaseAgent`` implements:

1.  **Prompt Assembly** — system prompt + grudge feedback + user message.
2.  **ReAct Loop** — Thought → Tool Call → Observation → repeat → Final Answer.
3.  **Safety Gating** — every tool call passes through the ``SafetyInterceptor``.
4.  **Memory** — conversation history is maintained per-session.

Each specialist (``@coder``, ``@sysadmin``) sub-classes ``BaseAgent``, only
overriding their name and allowed tools.  The loop logic is identical.
"""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from donna.config import get_settings
from donna.memory.feedback import read_feedback
from donna.models.base import (
    AbstractModel,
    AssistantMessage,
    Message,
    Role,
    ToolSchema,
)
from donna.safety.interceptor import SafetyInterceptor
from donna.tools.registry import get_tool_schemas

console = Console()

# Maximum number of tool-call steps before the agent gives up
MAX_STEPS = 15


class BaseAgent:
    """A ReAct agent that assembles prompts, calls models, and loops on tool results.

    Parameters
    ----------
    name : str
        Agent identifier (e.g. ``"coder"``).
    model : AbstractModel
        The LLM backend to use.
    safety : SafetyInterceptor
        Shared safety gate for tool execution.
    tool_names : list[str]
        Which registered tools this agent is allowed to use.
    """

    def __init__(
        self,
        name: str,
        model: AbstractModel,
        safety: SafetyInterceptor,
        tool_names: list[str] | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.safety = safety
        self.tool_names = tool_names or []

        # Load from config
        settings = get_settings()
        agent_cfg = settings.agents.get(name)

        if agent_cfg:
            self._system_prompt = agent_cfg.load_system_prompt()
            if not tool_names:
                self.tool_names = agent_cfg.tools
        else:
            self._system_prompt = f"You are @{name}, a helpful AI assistant."

    # ------------------------------------------------------------------
    # Prompt assembly
    # ------------------------------------------------------------------

    def _build_system_message(self) -> str:
        """Assemble the full system prompt with grudge feedback."""
        parts: list[str] = [self._system_prompt]

        # Inject grudge feedback
        feedback = read_feedback(self.name)
        if feedback:
            parts.append("\n\n## Past Corrections (IMPORTANT — follow these)\n")
            parts.append(feedback)

        return "\n".join(parts)

    def _get_tool_schemas(self) -> list[ToolSchema]:
        """Return the JSON schemas for this agent's allowed tools."""
        if not self.tool_names:
            return []
        return get_tool_schemas(self.tool_names)

    # ------------------------------------------------------------------
    # The ReAct loop
    # ------------------------------------------------------------------

    def run(self, user_message: str, history: list[Message] | None = None) -> str:
        """Execute the full ReAct loop for a user prompt.

        Parameters
        ----------
        user_message : str
            The user's input text.
        history : list[Message] | None
            Optional prior conversation history.

        Returns
        -------
        str
            The agent's final textual response.
        """
        # --- Build the message list ---
        messages: list[Message] = []

        # System prompt (with feedback)
        messages.append(Message(role=Role.SYSTEM, content=self._build_system_message()))

        # Prior conversation history
        if history:
            messages.extend(history)

        # Current user message
        messages.append(Message(role=Role.USER, content=user_message))

        # Tool schemas
        tools = self._get_tool_schemas()

        # --- ReAct loop ---
        for step in range(MAX_STEPS):
            response: AssistantMessage = self.model.chat(
                messages=messages,
                tools=tools if tools else None,
            )

            if not response.has_tool_calls:
                # No tool calls → this is the final answer
                return response.content

            # Append the assistant's response (once, before tool results)
            messages.append(Message(
                role=Role.ASSISTANT,
                content=response.content or "",
            ))

            # Process each tool call
            for tc in response.tool_calls:
                # Show what the agent is doing
                args_display = ", ".join(f"{k}={v!r}" for k, v in tc.arguments.items())
                console.print(
                    f"  [dim]🔧 @{self.name} → {tc.name}({args_display})[/dim]"
                )

                # Execute through safety gate
                result = self.safety.execute(tc)

                # Show truncated result
                preview = result[:200] + "..." if len(result) > 200 else result
                console.print(f"  [dim]   ↳ {preview}[/dim]")

                # Append tool result
                messages.append(Message(
                    role=Role.TOOL,
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.name,
                ))

        return (
            f"[Agent @{self.name} hit the step limit ({MAX_STEPS}). "
            "This usually means the task is too complex for a single pass.]"
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_response(self, response: str) -> None:
        """Pretty-print a response to the terminal using rich."""
        console.print()
        console.print(
            Panel(
                Markdown(response),
                title=f"[bold cyan]@{self.name}[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )
