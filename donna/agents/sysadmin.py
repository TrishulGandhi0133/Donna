"""
donna.agents.sysadmin — The @sysadmin specialist agent.

Specializes in system administration, package management,
process control, and OS-level operations.
Inherits the ReAct loop from ``BaseAgent``.
"""

from __future__ import annotations

from donna.agents.base_agent import BaseAgent
from donna.models.base import AbstractModel
from donna.safety.interceptor import SafetyInterceptor


class SysAdminAgent(BaseAgent):
    """System administration specialist — installs, processes, configs."""

    def __init__(self, model: AbstractModel, safety: SafetyInterceptor) -> None:
        super().__init__(name="sysadmin", model=model, safety=safety)
