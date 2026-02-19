"""Tests for donna.agents — router, base agent, and pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

from donna.agents.router import Router, VALID_AGENTS
from donna.agents.base_agent import BaseAgent
from donna.agents import AgentPipeline
from donna.models.base import (
    AbstractModel,
    AssistantMessage,
    Message,
    Role,
    ToolCall,
    ToolSchema,
)
from donna.safety.interceptor import SafetyInterceptor


# ---------------------------------------------------------------------------
# Helpers — mock model
# ---------------------------------------------------------------------------


def _make_mock_model(content: str = "Mock response.", tool_calls: list | None = None) -> MagicMock:
    """Create a mock model that returns a fixed response."""
    mock = MagicMock(spec=AbstractModel)
    response = AssistantMessage(
        content=content,
        tool_calls=tool_calls or [],
    )
    mock.chat.return_value = response
    return mock


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


class TestRouter:
    """Test the intent classifier / dispatcher."""

    def test_explicit_coder_tag(self) -> None:
        mock_model = _make_mock_model()
        router = Router(mock_model)
        agent, msg = router.route("@coder fix the build")
        assert agent == "coder"
        assert "fix the build" in msg

    def test_explicit_sysadmin_tag(self) -> None:
        mock_model = _make_mock_model()
        router = Router(mock_model)
        agent, msg = router.route("@sysadmin install nodejs")
        assert agent == "sysadmin"

    def test_keyword_routing_to_sysadmin(self) -> None:
        mock_model = _make_mock_model()
        router = Router(mock_model)
        agent, _ = router.route("install docker on this machine")
        assert agent == "sysadmin"

    def test_default_to_coder(self) -> None:
        """Ambiguous prompts should default to coder when LLM fails."""
        mock_model = _make_mock_model(content="I don't know")
        router = Router(mock_model)
        agent, _ = router.route("what is the meaning of life")
        assert agent == "coder"

    def test_valid_agents_contains_expected(self) -> None:
        assert "coder" in VALID_AGENTS
        assert "sysadmin" in VALID_AGENTS


# ---------------------------------------------------------------------------
# BaseAgent tests
# ---------------------------------------------------------------------------


class TestBaseAgent:
    """Test the ReAct agent loop with a mocked model."""

    def test_simple_text_response(self) -> None:
        """When the model returns text (no tool calls), loop should return it."""
        mock_model = _make_mock_model(content="The answer is 42.")
        safety = SafetyInterceptor()
        agent = BaseAgent(name="coder", model=mock_model, safety=safety)

        result = agent.run("What is the answer?")
        assert result == "The answer is 42."
        mock_model.chat.assert_called_once()

    def test_system_prompt_includes_feedback(self) -> None:
        """The system prompt should include grudge feedback if present."""
        from donna.memory.feedback import append_feedback, clear_feedback

        clear_feedback("_test_base_agent")
        append_feedback("_test_base_agent", "always use poetry")

        mock_model = _make_mock_model(content="ok")
        safety = SafetyInterceptor()
        agent = BaseAgent(name="_test_base_agent", model=mock_model, safety=safety)

        agent.run("test prompt")

        # Check the system message that was sent to the model
        call_args = mock_model.chat.call_args
        messages: list[Message] = call_args.kwargs.get("messages") or call_args.args[0]
        system_msg = messages[0]
        assert "always use poetry" in system_msg.content

        clear_feedback("_test_base_agent")

    def test_tool_call_loop(self) -> None:
        """When model returns a tool call, agent should execute it and loop."""
        mock_model = _make_mock_model()

        # First call: model wants to call a tool
        tool_response = AssistantMessage(
            content="",
            tool_calls=[
                ToolCall(id="tc1", name="list_dir", arguments={"path": "."})
            ],
        )
        # Second call: model returns final answer
        final_response = AssistantMessage(content="Here are your files.")

        mock_model.chat.side_effect = [tool_response, final_response]

        safety = SafetyInterceptor()
        agent = BaseAgent(
            name="coder",
            model=mock_model,
            safety=safety,
            tool_names=["list_dir"],
        )

        result = agent.run("list my files")
        assert result == "Here are your files."
        assert mock_model.chat.call_count == 2


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------


class TestAgentPipeline:
    """Test the full pipeline orchestration."""

    def test_pipeline_routes_and_responds(self) -> None:
        """Pipeline should route input and return a response."""
        mock_model = _make_mock_model(content="Fixed!")
        pipeline = AgentPipeline(mock_model)

        response = pipeline.handle("@coder fix the bug")
        assert response == "Fixed!"

    def test_pipeline_maintains_history(self) -> None:
        """Pipeline should accumulate conversation history per agent."""
        mock_model = _make_mock_model(content="Done.")
        pipeline = AgentPipeline(mock_model)

        pipeline.handle("@coder first message")
        pipeline.handle("@coder second message")

        # Coder history should have 2 exchanges (4 messages)
        assert len(pipeline._history["coder"]) == 4
