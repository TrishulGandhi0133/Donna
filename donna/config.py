"""
donna.config — Load, validate, and expose project configuration.

Reads `config/config.yaml` (relative to project root) and `.env`,
then validates everything through Pydantic models.  The module exposes
a single `get_settings()` function that returns a cached `DonnaSettings`
instance.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

# Project root = the directory containing pyproject.toml.
# We walk upward from this file (donna/config.py → donna/ → Donna/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure runtime data dirs exist
for _sub in ("feedback", "chroma", "skills"):
    (DATA_DIR / _sub).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class OllamaSettings(BaseModel):
    """Settings for the local Ollama LLM backend."""

    base_url: str = "http://localhost:11434"
    model: str = "llama3:8b"
    temperature: float = 0.2


class GroqSettings(BaseModel):
    """Settings for the Groq cloud LLM backend."""

    api_key: str = ""
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.3


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    model_config = {"protected_namespaces": ()}

    prompt: str                          # Relative path to system prompt file
    model_override: str | None = None
    tools: list[str] = Field(default_factory=list)

    def load_system_prompt(self) -> str:
        """Read the system prompt file from disk."""
        prompt_path = PROJECT_ROOT / self.prompt
        if not prompt_path.exists():
            raise FileNotFoundError(f"System prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")


class SafetySettings(BaseModel):
    """Red / Green classification rules."""

    red_keywords: list[str] = Field(default_factory=lambda: ["rm", "sudo", "del"])
    auto_approve_green: bool = True
    max_red_per_session: int = 10


class MemorySettings(BaseModel):
    """Feedback & vector-memory settings."""

    feedback_token_budget: int = 2000
    vector_top_k: int = 3
    chroma_path: str = "data/chroma"


class DonnaSettings(BaseModel):
    """Top-level settings object for the entire application."""

    version: int = 1
    default_model: str = "ollama"  # "ollama" | "groq"

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file.  Returns {} if not found."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_settings() -> DonnaSettings:
    """Return the validated, cached application settings.

    Loading order (each layer overrides the previous):
    1. Built-in defaults (Pydantic field defaults).
    2. ``config/config.yaml``.
    3. Environment variables / ``.env`` file.
    """

    # 1. Load .env (if present) so env-vars are available to Pydantic
    load_dotenv(PROJECT_ROOT / ".env")

    # 2. Parse YAML
    raw: dict[str, Any] = _load_yaml(CONFIG_DIR / "config.yaml")

    # 3. Overlay env-var overrides
    if api_key := os.getenv("GROQ_API_KEY"):
        raw.setdefault("groq", {})["api_key"] = api_key
    if model_override := os.getenv("DONNA_MODEL"):
        raw["default_model"] = model_override

    # 4. Validate through Pydantic
    return DonnaSettings(**raw)
