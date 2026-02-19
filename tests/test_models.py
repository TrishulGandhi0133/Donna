"""Tests for donna.models — data types, protocol, and backend construction."""

from __future__ import annotations

from donna.models.base import (
    AssistantMessage,
    Message,
    Role,
    ToolCall,
    ToolSchema,
    AbstractModel,
)
from donna.models.ollama_backend import OllamaModel
from donna.models.groq_backend import GroqModel


class TestDataTypes:
    """Verify the shared data types behave correctly."""

    def test_message_creation(self) -> None:
        msg = Message(role=Role.USER, content="hello")
        assert msg.role == Role.USER
        assert msg.content == "hello"

    def test_tool_call_defaults(self) -> None:
        tc = ToolCall(id="abc", name="read_file")
        assert tc.arguments == {}

    def test_tool_schema_creation(self) -> None:
        schema = ToolSchema(
            name="test_tool",
            description="A test tool.",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
        )
        assert schema.name == "test_tool"

    def test_assistant_message_no_tool_calls(self) -> None:
        msg = AssistantMessage(content="done")
        assert not msg.has_tool_calls
        assert msg.content == "done"

    def test_assistant_message_with_tool_calls(self) -> None:
        msg = AssistantMessage(
            content="",
            tool_calls=[ToolCall(id="1", name="read_file", arguments={"path": "x"})],
        )
        assert msg.has_tool_calls
        assert len(msg.tool_calls) == 1


class TestOllamaModel:
    """Verify OllamaModel can be constructed and satisfies the Protocol."""

    def test_construction(self) -> None:
        model = OllamaModel(base_url="http://localhost:11434", model="llama3:8b")
        assert model.model == "llama3:8b"
        assert model.temperature == 0.2

    def test_satisfies_protocol(self) -> None:
        """OllamaModel should be recognized as an AbstractModel."""
        assert isinstance(OllamaModel(), AbstractModel)

    def test_build_messages(self) -> None:
        """Internal message conversion should produce correct dicts."""
        model = OllamaModel()
        msgs = [
            Message(role=Role.SYSTEM, content="You are helpful."),
            Message(role=Role.USER, content="Hi"),
        ]
        converted = model._build_messages(msgs)
        assert len(converted) == 2
        assert converted[0]["role"] == "system"
        assert converted[1]["content"] == "Hi"

    def test_build_tools(self) -> None:
        """Tool schema conversion should produce OpenAI-style dicts."""
        model = OllamaModel()
        schemas = [
            ToolSchema(name="test", description="desc", parameters={"type": "object"})
        ]
        converted = model._build_tools(schemas)
        assert len(converted) == 1
        assert converted[0]["type"] == "function"
        assert converted[0]["function"]["name"] == "test"


class TestGroqModel:
    """Verify GroqModel construction."""

    def test_construction(self) -> None:
        model = GroqModel(api_key="gsk_test", model="llama-3.3-70b-versatile")
        assert model.model == "llama-3.3-70b-versatile"

    def test_satisfies_protocol(self) -> None:
        assert isinstance(GroqModel(api_key="test"), AbstractModel)

    def test_build_messages(self) -> None:
        msgs = [Message(role=Role.USER, content="hello")]
        converted = GroqModel._build_messages(msgs)
        assert converted[0]["role"] == "user"
        assert converted[0]["content"] == "hello"

    def test_build_tools(self) -> None:
        schemas = [
            ToolSchema(name="foo", description="bar", parameters={"type": "object"})
        ]
        converted = GroqModel._build_tools(schemas)
        assert converted[0]["function"]["name"] == "foo"
