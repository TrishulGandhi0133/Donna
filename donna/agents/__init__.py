"""
donna.agents — Agent orchestration package.

Exports:
    create_pipeline()   — one-call setup for the full router+agents+safety stack
    BaseAgent           — for advanced usage / subclassing
    Router, CoderAgent, SysAdminAgent, CriticAgent
"""

from donna.agents.base_agent import BaseAgent
from donna.agents.router import Router
from donna.agents.coder import CoderAgent
from donna.agents.sysadmin import SysAdminAgent
from donna.agents.critic import CriticAgent
from donna.models.base import AbstractModel, Message
from donna.safety.interceptor import SafetyInterceptor


class AgentPipeline:
    """Pre-wired pipeline: router + specialist agents + safety gate.

    Usage
    -----
    ::

        pipeline = create_pipeline(cloud=False)
        response = pipeline.handle("@coder fix the build error")
    """

    def __init__(self, model: AbstractModel) -> None:
        self.model = model
        self.safety = SafetyInterceptor()
        self.router = Router(model)
        self._agents: dict[str, BaseAgent] = {
            "coder": CoderAgent(model, self.safety),
            "sysadmin": SysAdminAgent(model, self.safety),
        }
        self.critic = CriticAgent(model, self.safety)

        # Per-agent conversation history (session-scoped)
        self._history: dict[str, list[Message]] = {name: [] for name in self._agents}
        # Shared conversation log — so agents know what happened before
        self._shared_log: list[dict[str, str]] = []

    def handle(self, user_input: str, use_critic: bool = False) -> str:
        """Route the input to the correct agent and return the response.

        Parameters
        ----------
        user_input : str
            Raw user input (may include @tags).
        use_critic : bool
            If True, run the response through @critic before returning.

        Returns
        -------
        str
            The agent's (or critic-reviewed) response.
        """
        # 1. Route
        agent_name, cleaned_msg = self.router.route(user_input)
        agent = self._agents.get(agent_name)
        if agent is None:
            agent = self._agents["coder"]
            agent_name = "coder"

        # 2. Build cross-agent context if there's prior conversation
        augmented_msg = cleaned_msg
        if self._shared_log:
            # Include recent conversation context so the agent knows
            # what happened with other agents
            recent = self._shared_log[-3:]  # Last 3 exchanges
            context_lines = []
            for entry in recent:
                context_lines.append(
                    f"[@{entry['agent']}] User asked: {entry['user']}\n"
                    f"[@{entry['agent']}] Responded: {entry['response'][:500]}"
                )
            context = "\n\n".join(context_lines)
            augmented_msg = (
                f"[Previous conversation context]\n{context}\n\n"
                f"[Current request]\n{cleaned_msg}"
            )

        # 3. Run the ReAct loop
        response = agent.run(
            user_message=augmented_msg,
            history=self._history.get(agent_name),
        )

        # 4. Optional critic review
        if use_critic and response:
            response = self.critic.review(response, cleaned_msg)

        # 5. Update session history
        from donna.models.base import Role
        self._history.setdefault(agent_name, []).extend([
            Message(role=Role.USER, content=cleaned_msg),
            Message(role=Role.ASSISTANT, content=response),
        ])

        # 6. Update shared log
        self._shared_log.append({
            "agent": agent_name,
            "user": cleaned_msg,
            "response": response,
        })

        # 7. Render
        agent.render_response(response)

        return response


def create_pipeline(cloud: bool = False) -> AgentPipeline:
    """Factory: create a fully-wired agent pipeline.

    Parameters
    ----------
    cloud : bool
        If True, use Groq cloud backend; else Ollama local.
    """
    from donna.models import get_model

    model = get_model(cloud=cloud)
    return AgentPipeline(model)


__all__ = [
    "AgentPipeline",
    "create_pipeline",
    "BaseAgent",
    "Router",
    "CoderAgent",
    "SysAdminAgent",
    "CriticAgent",
]
