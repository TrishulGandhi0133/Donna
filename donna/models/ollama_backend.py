"""
donna.models.ollama_backend — Local LLM backend via Ollama.

Connects to a running Ollama instance (default ``http://localhost:11434``)
and translates between Donna's ``AbstractModel`` contract and Ollama's
``/api/chat`` REST API.

**How it works:**

1.  Donna's ``Message`` list is converted into Ollama's message format.
2.  If tools are provided, they are sent as JSON schemas so the model
    can make function calls.
3.  Ollama's response is parsed back into an ``AssistantMessage``,
    extracting any ``tool_calls`` the model requested.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx

from donna.models.base import (
    AbstractModel,
    AssistantMessage,
    Message,
    Role,
    ToolCall,
    ToolSchema,
)


class OllamaModel:
    """Ollama LLM backend.

    Parameters
    ----------
    base_url : str
        Ollama server URL (e.g. ``http://localhost:11434``).
    model : str
        Model tag to use (e.g. ``llama3:8b``).
    temperature : float
        Sampling temperature (0.0 = deterministic, 1.0 = creative).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3:8b",
        temperature: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self._client = httpx.Client(timeout=120.0)

    # ---- internal helpers ------------------------------------------------

    @staticmethod
    def _role_str(role: Role) -> str:
        """Convert our Role enum to Ollama's role string."""
        return role.value

    def _build_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Donna messages → Ollama message dicts."""
        out: list[dict[str, Any]] = []
        for m in messages:
            entry: dict[str, Any] = {
                "role": self._role_str(m.role),
                "content": m.content,
            }
            out.append(entry)
        return out

    def _build_tools(self, tools: list[ToolSchema]) -> list[dict[str, Any]]:
        """Convert Donna ToolSchemas → Ollama tool definitions."""
        out: list[dict[str, Any]] = []
        for t in tools:
            out.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
            )
        return out

    def _parse_tool_calls(self, raw_msg: dict[str, Any]) -> list[ToolCall]:
        """Extract tool calls from Ollama's response message."""
        calls: list[ToolCall] = []
        for tc in raw_msg.get("tool_calls", []):
            func = tc.get("function", {})
            args = func.get("arguments", {})
            # Some models return args as a JSON string
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"raw": args}
            calls.append(
                ToolCall(
                    id=str(uuid.uuid4()),
                    name=func.get("name", "unknown"),
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
        """Send a conversation to Ollama and return the response."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._build_messages(messages),
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        if tools:
            payload["tools"] = self._build_tools(tools)

        resp = self._client.post(f"{self.base_url}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

        raw_msg = data.get("message", {})
        content = raw_msg.get("content", "")
        tool_calls = self._parse_tool_calls(raw_msg)

        return AssistantMessage(
            content=content,
            tool_calls=tool_calls,
            raw=data,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    # Make it usable as a context manager
    def __enter__(self) -> "OllamaModel":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# Satisfy the Protocol at module level (for static type checkers)
_: type[AbstractModel] = OllamaModel  # type: ignore[assignment]
