"""
donna.agents.critic — The @critic auditor agent.

Reviews another agent's draft response before it reaches the user.
Has no tools — it's text-only.  It can approve (pass-through) or
edit the response.
"""

from __future__ import annotations

from donna.agents.base_agent import BaseAgent
from donna.models.base import AbstractModel, Message, Role
from donna.safety.interceptor import SafetyInterceptor


class CriticAgent(BaseAgent):
    """Output auditor — reviews and optionally refines responses."""

    def __init__(self, model: AbstractModel, safety: SafetyInterceptor) -> None:
        super().__init__(name="critic", model=model, safety=safety, tool_names=[])

    def review(self, original_response: str, user_prompt: str) -> str:
        """Review a draft response and return a refined version.

        Parameters
        ----------
        original_response : str
            The specialist agent's draft response.
        user_prompt : str
            The original user request (provides context).

        Returns
        -------
        str
            The reviewed (and possibly edited) response.
        """
        review_prompt = (
            f"The user asked: \"{user_prompt}\"\n\n"
            f"A specialist agent produced this response:\n\n"
            f"---\n{original_response}\n---\n\n"
            "Review it. If it's good, return it unchanged. "
            "If it needs corrections, return the corrected version."
        )
        return self.run(review_prompt)
