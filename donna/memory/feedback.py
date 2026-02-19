"""
donna.memory.feedback — The "Grudge" memory system.

Each agent has its own ``feedback.md`` file under ``data/feedback/``.
When the user provides a correction (e.g. "don't use pip, use poetry"),
it is timestamped and appended here.  Before every generation, the agent
reads its feedback file and prepends the contents to the system prompt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from donna.config import DATA_DIR

FEEDBACK_DIR = DATA_DIR / "feedback"
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def _feedback_path(agent_name: str) -> Path:
    """Return the path to an agent's feedback file."""
    return FEEDBACK_DIR / f"{agent_name}.md"


def append_feedback(agent_name: str, text: str) -> None:
    """Append a timestamped correction to the agent's feedback file.

    Parameters
    ----------
    agent_name:
        The agent this feedback applies to (e.g. ``"coder"``).
    text:
        The correction text supplied by the user.
    """
    path = _feedback_path(agent_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"- [{timestamp}] {text}\n"

    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)


def read_feedback(agent_name: str) -> str:
    """Read all feedback entries for an agent.

    Returns an empty string if no feedback exists yet.
    """
    path = _feedback_path(agent_name)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def clear_feedback(agent_name: str) -> None:
    """Delete all feedback for an agent (mainly for testing)."""
    path = _feedback_path(agent_name)
    if path.exists():
        path.unlink()
