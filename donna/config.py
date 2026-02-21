"""
donna.config — Load, validate, and expose project configuration.

Config search order (first found wins):
1. ``~/.donna/config.yaml``  (user-level, created by ``donna setup``)
2. ``./config/config.yaml``  (project-level, for development)
3. Built-in Pydantic defaults

Environment variables override everything (``GROQ_API_KEY``, ``DONNA_MODEL``).
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

# User-level config directory
DONNA_HOME = Path.home() / ".donna"

# Project root (dev mode) = directory containing pyproject.toml
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_DIR = PROJECT_ROOT / "config"

# Resolve config and data directories based on what exists
if (DONNA_HOME / "config.yaml").exists():
    # User installed via pip + ran donna setup
    CONFIG_DIR = DONNA_HOME
    DATA_DIR = DONNA_HOME / "data"
    _ENV_FILE = DONNA_HOME / ".env"
else:
    # Developer mode — project-relative paths
    CONFIG_DIR = PROJECT_CONFIG_DIR
    DATA_DIR = PROJECT_ROOT / "data"
    _ENV_FILE = PROJECT_ROOT / ".env"

# Ensure runtime data dirs exist
for _sub in ("feedback", "chroma", "skills"):
    (DATA_DIR / _sub).mkdir(parents=True, exist_ok=True)

# Prompts are always in the project's config/prompts/ (shipped with package)
PROMPTS_DIR = PROJECT_CONFIG_DIR / "prompts"


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
        """Read the system prompt file from disk.

        Searches in order:
        1. Relative to project root (covers both dev and installed modes)
        2. Relative to DONNA_HOME
        """
        # Try project root first (handles both dev + installed package)
        prompt_path = PROJECT_ROOT / self.prompt
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")

        # Fallback: user-level config
        prompt_path = DONNA_HOME / self.prompt
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")

        raise FileNotFoundError(f"System prompt not found: {self.prompt}")


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


def needs_setup() -> bool:
    """Return True if neither user-level nor project-level config exists."""
    user_config = DONNA_HOME / "config.yaml"
    project_config = PROJECT_CONFIG_DIR / "config.yaml"
    project_env = PROJECT_ROOT / ".env"

    # If project .env or config exists, we're in dev mode — no setup needed
    if project_config.exists() and project_env.exists():
        return False

    return not user_config.exists()


@lru_cache(maxsize=1)
def get_settings() -> DonnaSettings:
    """Return the validated, cached application settings.

    Loading order (each layer overrides the previous):
    1. Built-in defaults (Pydantic field defaults).
    2. Config YAML (user-level ``~/.donna/`` or project-level ``config/``).
    3. Environment variables / ``.env`` file.
    """

    # 1. Load .env (if present) so env-vars are available to Pydantic
    load_dotenv(_ENV_FILE)

    # 2. Parse YAML — try user-level first, fallback to project-level
    config_path = CONFIG_DIR / "config.yaml"
    raw: dict[str, Any] = _load_yaml(config_path)

    # 3. Overlay env-var overrides
    if api_key := os.getenv("GROQ_API_KEY"):
        raw.setdefault("groq", {})["api_key"] = api_key
    if model_override := os.getenv("DONNA_MODEL"):
        raw["default_model"] = model_override

    # 4. Validate through Pydantic
    return DonnaSettings(**raw)
