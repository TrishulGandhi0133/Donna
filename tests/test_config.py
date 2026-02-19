"""Tests for donna.config — settings loading and validation."""

from __future__ import annotations

from donna.config import get_settings, DonnaSettings, OllamaSettings, GroqSettings


class TestDonnaSettings:
    """Unit tests for the config loader."""

    def test_get_settings_returns_donna_settings(self) -> None:
        """get_settings() should return a DonnaSettings instance."""
        settings = get_settings()
        assert isinstance(settings, DonnaSettings)

    def test_default_model_is_set(self) -> None:
        """default_model should be one of the known backends."""
        settings = get_settings()
        assert settings.default_model in ("ollama", "groq")

    def test_ollama_settings_populated(self) -> None:
        """Ollama settings should have sensible defaults."""
        settings = get_settings()
        assert isinstance(settings.ollama, OllamaSettings)
        assert settings.ollama.base_url.startswith("http")
        assert len(settings.ollama.model) > 0

    def test_groq_settings_populated(self) -> None:
        """Groq settings should exist (key may be empty)."""
        settings = get_settings()
        assert isinstance(settings.groq, GroqSettings)
        assert len(settings.groq.model) > 0

    def test_agents_loaded(self) -> None:
        """At least the core agents should be defined in config."""
        settings = get_settings()
        assert "router" in settings.agents
        assert "coder" in settings.agents
        assert "sysadmin" in settings.agents
        assert "critic" in settings.agents

    def test_agent_system_prompt_loadable(self) -> None:
        """Each agent's system prompt file should exist and be loadable."""
        settings = get_settings()
        for name, agent_cfg in settings.agents.items():
            prompt_text = agent_cfg.load_system_prompt()
            assert len(prompt_text) > 0, f"@{name} system prompt is empty"

    def test_safety_red_keywords(self) -> None:
        """Safety config should contain at least some red keywords."""
        settings = get_settings()
        assert len(settings.safety.red_keywords) > 0
        assert "rm" in settings.safety.red_keywords

    def test_memory_settings(self) -> None:
        """Memory settings should have positive values."""
        settings = get_settings()
        assert settings.memory.feedback_token_budget > 0
        assert settings.memory.vector_top_k > 0
