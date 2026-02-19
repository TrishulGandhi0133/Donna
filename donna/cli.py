"""
donna.cli — Typer-based CLI entry-point.

This is what runs when a user types `donna` in their terminal.
Sub-commands:

    donna chat                  → interactive REPL
    donna run "fix the tests"   → one-shot prompt (Phase 3)
    donna watch                 → enter recording mode (Phase 4)
    donna feedback "..."        → append a correction to the active agent
    donna info                  → print current config summary
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from donna import __version__
from donna.config import get_settings

# ---------------------------------------------------------------------------
# Typer app
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="donna",
    help="Donna — Digital Operative for Non-Negotiable Automation.",
    no_args_is_help=True,
    add_completion=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Callbacks (version flag)
# ---------------------------------------------------------------------------

def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]donna[/bold cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Donna — your CLI-resident AI agent framework."""


# ---------------------------------------------------------------------------
# donna info
# ---------------------------------------------------------------------------

@app.command()
def info() -> None:
    """Print the current configuration summary."""
    settings = get_settings()

    model_name = (
        f"{settings.ollama.model} (Ollama)"
        if settings.default_model == "ollama"
        else f"{settings.groq.model} (Groq)"
    )

    agents_list = ", ".join(f"@{name}" for name in settings.agents)

    body = Text.assemble(
        ("Model:   ", "bold"),
        (model_name, "green"),
        "\n",
        ("Agents:  ", "bold"),
        (agents_list or "(none)", "cyan"),
        "\n",
        ("Safety:  ", "bold"),
        (f"{len(settings.safety.red_keywords)} red keywords", "red"),
        "\n",
    )

    console.print(
        Panel(body, title=f"[bold]Donna v{__version__}[/bold]", border_style="bright_blue")
    )


# ---------------------------------------------------------------------------
# donna chat  (interactive REPL — delegates to shell.py)
# ---------------------------------------------------------------------------

@app.command()
def chat(
    cloud: bool = typer.Option(False, "--cloud", help="Use Groq cloud model instead of Ollama."),
    agent: Optional[str] = typer.Option(  # noqa: UP007
        None, "--agent", "-a", help="Pin conversation to a specific agent (e.g. coder)."
    ),
) -> None:
    """Start an interactive chat session with Donna."""
    from donna.shell import start_repl   # lazy import to keep startup fast

    start_repl(cloud=cloud, pinned_agent=agent)


# ---------------------------------------------------------------------------
# donna run  (one-shot — placeholder for Phase 3)
# ---------------------------------------------------------------------------

@app.command()
def run(
    prompt: str = typer.Argument(..., help="The prompt to send to Donna."),
    cloud: bool = typer.Option(False, "--cloud", help="Use Groq cloud model."),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Target agent."),  # noqa: UP007
) -> None:
    """Run a single prompt and exit (non-interactive)."""
    from donna.agents import create_pipeline

    # Pin to agent if specified
    full_prompt = f"@{agent} {prompt}" if agent else prompt

    try:
        pipeline = create_pipeline(cloud=cloud)
        pipeline.handle(full_prompt)
    except Exception as exc:
        console.print(f"[red]✗ Error: {type(exc).__name__}: {exc}[/red]")
        console.print("[dim]If using Ollama, make sure it's running. Try --cloud for Groq.[/dim]")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# donna watch  (placeholder for Phase 4)
# ---------------------------------------------------------------------------

@app.command()
def watch() -> None:
    """Enter Watch & Learn recording mode."""
    # TODO: Phase 4
    console.print("[yellow]⚠  Watch mode not yet implemented (coming in Phase 4).[/yellow]")


# ---------------------------------------------------------------------------
# donna feedback
# ---------------------------------------------------------------------------

@app.command()
def feedback(
    correction: str = typer.Argument(..., help="The correction to record."),
    agent: str = typer.Option("coder", "--agent", "-a", help="Which agent this feedback is for."),
) -> None:
    """Append a correction to an agent's feedback memory."""
    from donna.memory.feedback import append_feedback  # lazy import

    append_feedback(agent_name=agent, text=correction)
    console.print(f"[green]✓[/green] Correction saved for [bold]@{agent}[/bold].")


# ---------------------------------------------------------------------------
# Entry-point (for `python -m donna.cli`)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
