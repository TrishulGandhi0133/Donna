"""
donna.models.groq_backend — Cloud LLM backend via Groq API.

Groq exposes an **OpenAI-compatible** API, so we use the ``openai`` SDK
pointed at ``https://api.groq.com/openai/v1``.  This is the "cloud
fallback" when you need raw speed or a larger model than what fits
locally.

**How it works:**

1.  Donna's ``Message`` list is converted into OpenAI-format dicts.
2.  Tool schemas are sent as OpenAI-style function definitions.
3.  The response is parsed back into our ``AssistantMessage``, with
    any ``tool_calls`` extracted.
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from donna.models.base import (
    AbstractModel,
    AssistantMessage,
    Message,
    Role,
    ToolCall,
    ToolSchema,
)


class GroqModel:
    """Groq cloud LLM backend (OpenAI-compatible).

    Parameters
    ----------
    api_key : str
        Your Groq API key (starts with ``gsk_``).
    model : str
        Model to use (e.g. ``llama-3.3-70b-versatile``).
    temperature : float
        Sampling temperature.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    # ---- internal helpers ------------------------------------------------

    @staticmethod
    def _build_messages(messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Donna messages → OpenAI-format message dicts."""
        out: list[dict[str, Any]] = []
        for m in messages:
            entry: dict[str, Any] = {
                "role": m.role.value,
                "content": m.content,
            }
            if m.role == Role.TOOL:
                entry["tool_call_id"] = m.tool_call_id or ""
                entry["name"] = m.name or ""
            out.append(entry)
        return out

    @staticmethod
    def _build_tools(tools: list[ToolSchema]) -> list[dict[str, Any]]:
        """Convert Donna ToolSchemas → OpenAI-format tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    @staticmethod
    def _parse_tool_calls(choice: Any) -> list[ToolCall]:
        """Extract tool calls from an OpenAI ChatCompletion choice."""
        calls: list[ToolCall] = []
        raw_calls = getattr(choice.message, "tool_calls", None) or []
        for tc in raw_calls:
            args = tc.function.arguments
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"raw": args}
            calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                )
            )
        return calls

    # ---- public interface ------------------------------------------------

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
    ) -> AssistantMessage:
        """Send a conversation to Groq and return the response."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._build_messages(messages),
            "temperature": self.temperature,
        }

        if tools:
            kwargs["tools"] = self._build_tools(tools)

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        content = choice.message.content or ""
        tool_calls = self._parse_tool_calls(choice)

        return AssistantMessage(
            content=content,
            tool_calls=tool_calls,
            raw=response.model_dump(),
        )


# Satisfy the Protocol at module level
_: type[AbstractModel] = GroqModel  # type: ignore[assignment]
