"""
donna.models.base — Model-agnostic LLM abstraction.

Defines the ``AbstractModel`` protocol and shared data types that all
backends (Ollama, Groq, future providers) implement.  No concrete LLM
logic lives here — just the contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Shared data types
# ---------------------------------------------------------------------------


class Role(str, Enum):
    """Message roles in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in a conversation.

    Attributes
    ----------
    role : Role
        Who produced this message.
    content : str
        The textual content.
    tool_call_id : str | None
        If this is a TOOL result, the id of the tool call it answers.
    name : str | None
        Optional name attached to the message (e.g. tool name).
    """

    role: Role
    content: str
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolCall:
    """A tool invocation requested by the model.

    Attributes
    ----------
    id : str
        Unique identifier for this call (used to correlate results).
    name : str
        Name of the tool function to invoke.
    arguments : dict[str, Any]
        Parsed arguments to pass to the tool function.
    """

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSchema:
    """JSON-schema description of a tool that is sent to the model.

    Attributes
    ----------
    name : str
        Tool function name.
    description : str
        What the tool does (shown to the model).
    parameters : dict[str, Any]
        JSON Schema for the function's parameters.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssistantMessage:
    """The model's response — may contain text, tool calls, or both.

    Attributes
    ----------
    content : str
        The textual response (may be empty if the model only made tool calls).
    tool_calls : list[ToolCall]
        Zero or more tool invocations requested by the model.
    raw : dict[str, Any]
        The unmodified response from the provider (for debugging).
    """

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        """Return True if the model wants to invoke tools."""
        return len(self.tool_calls) > 0


# ---------------------------------------------------------------------------
# Abstract model protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AbstractModel(Protocol):
    """Contract that every LLM backend must satisfy.

    Backends simply implement ``chat()`` — the agent loop handles
    everything else (tool dispatch, safety gating, memory injection).
    """

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
    ) -> AssistantMessage:
        """Send a conversation to the model and return its response.

        Parameters
        ----------
        messages :
            The full conversation history (system + user + assistant + tool).
        tools :
            Optional list of tool schemas the model may invoke.

        Returns
        -------
        AssistantMessage
            The model's reply, potentially containing tool calls.
        """
        ...
