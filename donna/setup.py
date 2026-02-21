"""
donna.setup — First-run interactive setup wizard.

Creates ``~/.donna/`` with user-level config so Donna works after
``pip install donna-cli && donna setup``.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

# Canonical user-level config directory
DONNA_HOME = Path.home() / ".donna"
USER_CONFIG_PATH = DONNA_HOME / "config.yaml"
USER_ENV_PATH = DONNA_HOME / ".env"


def _ensure_donna_home() -> None:
    """Create ``~/.donna/`` and its subdirectories if they don't exist."""
    for sub in ("data/feedback", "data/chroma", "data/skills"):
        (DONNA_HOME / sub).mkdir(parents=True, exist_ok=True)


def _default_config() -> dict:
    """Return the default config dictionary."""
    return {
        "version": 1,
        "default_model": "ollama",
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3.1",
            "temperature": 0.2,
        },
        "groq": {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.3,
        },
        "agents": {
            "router": {
                "prompt": "config/prompts/router.txt",
                "model_override": None,
                "tools": [],
            },
            "coder": {
                "prompt": "config/prompts/coder.txt",
                "model_override": None,
                "tools": [
                    "read_file", "write_file", "list_dir",
                    "find_files", "execute_shell",
                ],
            },
            "sysadmin": {
                "prompt": "config/prompts/sysadmin.txt",
                "model_override": None,
                "tools": [
                    "execute_shell", "read_file", "write_file",
                    "delete_file", "list_dir", "find_files",
                    "launch_app", "kill_process",
                ],
            },
            "critic": {
                "prompt": "config/prompts/critic.txt",
                "model_override": None,
                "tools": [],
            },
        },
        "safety": {
            "red_keywords": ["rm", "sudo", "del", "format", "mkfs", ">"],
            "auto_approve_green": True,
            "max_red_per_session": 10,
        },
        "memory": {
            "feedback_token_budget": 2000,
            "vector_top_k": 3,
            "chroma_path": "data/chroma",
        },
    }


def is_configured() -> bool:
    """Return True if ``~/.donna/config.yaml`` exists."""
    return USER_CONFIG_PATH.exists()


def run_setup(reset: bool = False) -> None:
    """Interactive first-run wizard.

    Parameters
    ----------
    reset : bool
        If True, overwrite existing config.
    """
    if is_configured() and not reset:
        console.print("[green]✓[/green] Donna is already configured.")
        console.print(f"  Config: [dim]{USER_CONFIG_PATH}[/dim]")
        console.print("  Run [bold]donna setup --reset[/bold] to reconfigure.")
        return

    console.print()
    console.print(
        Panel(
            "[bold]Welcome to Donna![/bold]\n\n"
            "Let's set you up. This takes ~30 seconds.\n"
            "You'll need a [cyan]Groq API key[/cyan] for cloud mode,\n"
            "or [cyan]Ollama[/cyan] running locally for local mode.",
            title="🚀 First-Time Setup",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )
    console.print()

    # --- Step 1: Groq API key ---
    console.print("[bold]1/3[/bold] [cyan]Groq Cloud Setup[/cyan]")
    console.print("  Get a free key at: [link]https://console.groq.com/keys[/link]")
    groq_key = Prompt.ask(
        "  Groq API key (press Enter to skip)",
        default="",
        show_default=False,
    ).strip()

    # --- Step 2: Ollama model ---
    console.print()
    console.print("[bold]2/3[/bold] [cyan]Ollama Local Setup[/cyan]")
    console.print("  Install Ollama from: [link]https://ollama.com[/link]")
    ollama_model = Prompt.ask(
        "  Ollama model name",
        default="llama3.1",
    ).strip()

    ollama_url = Prompt.ask(
        "  Ollama URL",
        default="http://localhost:11434",
    ).strip()

    # --- Step 3: Default mode ---
    console.print()
    console.print("[bold]3/3[/bold] [cyan]Default Mode[/cyan]")
    default_mode = Prompt.ask(
        "  Preferred default mode",
        choices=["local", "cloud"],
        default="cloud" if groq_key else "local",
    )

    # --- Save config ---
    _ensure_donna_home()

    config = _default_config()
    config["default_model"] = "groq" if default_mode == "cloud" else "ollama"
    config["ollama"]["model"] = ollama_model
    config["ollama"]["base_url"] = ollama_url

    # Write YAML config
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Write .env with API key
    env_lines = []
    if groq_key:
        env_lines.append(f"GROQ_API_KEY={groq_key}")
    env_lines.append("")  # trailing newline
    USER_ENV_PATH.write_text("\n".join(env_lines), encoding="utf-8")

    console.print()
    console.print(
        Panel(
            f"[green]✓[/green] Config saved to [bold]{USER_CONFIG_PATH}[/bold]\n"
            f"[green]✓[/green] API key saved to [bold]{USER_ENV_PATH}[/bold]\n\n"
            "Try it now:\n"
            f"  [bold cyan]donna chat {'--cloud' if default_mode == 'cloud' else ''}[/bold cyan]",
            title="✅ Setup Complete",
            border_style="green",
            padding=(1, 2),
        )
    )
