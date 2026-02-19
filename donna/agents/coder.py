"""
donna.agents.coder — The @coder specialist agent.

Specializes in code, debugging, git, and file operations.
Inherits the ReAct loop from ``BaseAgent``.
"""

from __future__ import annotations

from donna.agents.base_agent import BaseAgent
from donna.models.base import AbstractModel
from donna.safety.interceptor import SafetyInterceptor


class CoderAgent(BaseAgent):
    """Code specialist — debugging, git, file manipulation."""

    def __init__(self, model: AbstractModel, safety: SafetyInterceptor) -> None:
        super().__init__(name="coder", model=model, safety=safety)
