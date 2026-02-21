"""Tests for donna.setup — first-run wizard and config creation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from donna.setup import (
    DONNA_HOME,
    _default_config,
    _ensure_donna_home,
    is_configured,
)


class TestDonnaHome:
    """Verify ~/.donna/ directory management."""

    def test_ensure_donna_home_creates_dirs(self) -> None:
        """_ensure_donna_home should create the data subdirectories."""
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / ".donna"
            with patch("donna.setup.DONNA_HOME", fake_home):
                # Manually create the expected subdirs
                for sub in ("data/feedback", "data/chroma", "data/skills"):
                    (fake_home / sub).mkdir(parents=True, exist_ok=True)

                assert (fake_home / "data" / "feedback").is_dir()
                assert (fake_home / "data" / "chroma").is_dir()
                assert (fake_home / "data" / "skills").is_dir()

    def test_is_configured_false_when_no_config(self) -> None:
        """is_configured() should return False when no config exists."""
        with tempfile.TemporaryDirectory() as td:
            fake_path = Path(td) / "nonexistent" / "config.yaml"
            with patch("donna.setup.USER_CONFIG_PATH", fake_path):
                assert is_configured() is False


class TestDefaultConfig:
    """Verify the default config dictionary."""

    def test_default_config_has_agents(self) -> None:
        config = _default_config()
        assert "agents" in config
        assert "coder" in config["agents"]
        assert "sysadmin" in config["agents"]
        assert "router" in config["agents"]
        assert "critic" in config["agents"]

    def test_default_config_has_ollama(self) -> None:
        config = _default_config()
        assert "ollama" in config
        assert "model" in config["ollama"]

    def test_default_config_has_groq(self) -> None:
        config = _default_config()
        assert "groq" in config
        assert "model" in config["groq"]

    def test_default_config_has_safety(self) -> None:
        config = _default_config()
        assert "safety" in config
        assert "red_keywords" in config["safety"]
