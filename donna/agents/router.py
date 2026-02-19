"""
donna.agents.router — The lightweight dispatcher agent.

``@router`` looks at the user's message and decides which specialist
should handle it.  It does this in two ways:

1.  **Tag detection** — if the user wrote ``@coder`` or ``@sysadmin``,
    skip the LLM and route directly.
2.  **LLM classification** — send the message to a fast model and ask
    it to return ``{"route": "coder"}`` or ``{"route": "sysadmin"}``.

If all else fails, it defaults to ``@coder``.
"""

from __future__ import annotations

import json
import re

from donna.models.base import AbstractModel, Message, Role


# Agent names that can be routed to
VALID_AGENTS = {"coder", "sysadmin"}

# Quick keyword patterns for fast routing (no LLM needed)
_SYSADMIN_KEYWORDS = re.compile(
    r"\b(install|process|kill|launch|open|sys|admin|sudo|"
    r"apt|brew|choco|service|daemon|port|network|dns|ssh)\b",
    re.IGNORECASE,
)


class Router:
    """Intent classifier and dispatcher.

    Parameters
    ----------
    model : AbstractModel
        LLM backend for ambiguous routing.
    """

    def __init__(self, model: AbstractModel) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, user_input: str) -> tuple[str, str]:
        """Determine which agent should handle the input.

        Returns
        -------
        tuple[str, str]
            ``(agent_name, cleaned_message)`` — the agent to dispatch to
            and the message with the @tag stripped.
        """
        # 1. Explicit @tag detection
        for agent_name in VALID_AGENTS:
            tag = f"@{agent_name}"
            if tag in user_input.lower():
                cleaned = user_input.replace(tag, "").replace(tag.capitalize(), "").strip()
                return agent_name, cleaned or user_input

        # 2. Keyword heuristic (fast, no LLM call)
        if _SYSADMIN_KEYWORDS.search(user_input):
            return "sysadmin", user_input

        # 3. LLM classification (fallback)
        try:
            return self._llm_classify(user_input), user_input
        except Exception:
            # If the LLM call fails, default to coder
            return "coder", user_input

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _llm_classify(self, user_input: str) -> str:
        """Ask the LLM to classify the intent."""
        from donna.config import get_settings

        settings = get_settings()
        router_cfg = settings.agents.get("router")
        system_prompt = router_cfg.load_system_prompt() if router_cfg else (
            "Classify the user's intent. Respond with ONLY a JSON object: "
            '{"route": "coder"} or {"route": "sysadmin"}.'
        )

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_input),
        ]

        response = self.model.chat(messages=messages)
        text = response.content.strip()

        # Parse JSON from response
        try:
            data = json.loads(text)
            route = data.get("route", "coder")
            if route in VALID_AGENTS:
                return route
        except json.JSONDecodeError:
            # Try to find JSON in the response
            match = re.search(r'\{[^}]+\}', text)
            if match:
                try:
                    data = json.loads(match.group())
                    route = data.get("route", "coder")
                    if route in VALID_AGENTS:
                        return route
                except json.JSONDecodeError:
                    pass

        return "coder"  # Safe default
