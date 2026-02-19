"""
donna.shell — Interactive REPL powered by prompt_toolkit + rich.

Launched by ``donna chat``.  Provides:
- @agent tag-completion
- Multi-line input (Alt+Enter to submit)
- Rich-rendered markdown/code output
- Session history (in-memory, per session)
"""

from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from donna import __version__
from donna.config import get_settings

console = Console()


def _build_completer() -> WordCompleter:
    """Build a tab-completer for @agent names and shortcut commands."""
    settings = get_settings()
    words = [f"@{name}" for name in settings.agents]
    words += ["@fix", "@explain", "exit", "quit", "help"]
    return WordCompleter(words, ignore_case=True)


def _print_welcome(cloud: bool, pinned_agent: str | None) -> None:
    """Print the welcome banner."""
    settings = get_settings()
    model = (
        f"{settings.groq.model} (Groq ☁️)"
        if cloud
        else f"{settings.ollama.model} (Ollama 🏠)"
    )
    pin_msg = f"  Pinned: @{pinned_agent}" if pinned_agent else ""

    console.print(
        Panel(
            f"[bold]Model:[/bold] {model}{pin_msg}\n"
            f"[dim]Type [bold]help[/bold] for commands, [bold]exit[/bold] to quit.[/dim]",
            title=f"[bold bright_blue]Donna v{__version__}[/bold bright_blue]",
            subtitle="[dim]Local-First • Privacy-Obsessed • Judgmental[/dim]",
            border_style="bright_blue",
        )
    )


_HELP_TEXT = """\
**Available commands**

| Command | Description |
|---------|-------------|
| `@coder <msg>` | Route to the coder agent |
| `@sysadmin <msg>` | Route to the sysadmin agent |
| `@fix` | Send clipboard content for debugging |
| `@explain` | Explain clipboard content |
| `help` | Show this help |
| `exit` / `quit` | Leave the REPL |

*Tip: Press **Tab** for auto-completion.*
"""


def start_repl(cloud: bool = False, pinned_agent: str | None = None) -> None:
    """Run the interactive REPL loop.

    Parameters
    ----------
    cloud:
        If True, use Groq cloud backend instead of Ollama.
    pinned_agent:
        If set, skip routing and always use this agent.
    """

    _print_welcome(cloud=cloud, pinned_agent=pinned_agent)

    session: PromptSession[str] = PromptSession(
        history=InMemoryHistory(),
        completer=_build_completer(),
        complete_while_typing=True,
    )

    while True:
        try:
            user_input: str = session.prompt(
                HTML("<b><ansicyan>donna ▸ </ansicyan></b>")
            ).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        # ----- built-in commands ----- #
        lower = user_input.lower()
        if lower in ("exit", "quit"):
            console.print("[dim]Goodbye.[/dim]")
            break

        if lower == "help":
            console.print(Markdown(_HELP_TEXT))
            continue

        # ----- agent dispatch (placeholder until Phase 3) ----- #
        console.print(
            Panel(
                f"[dim]Your message:[/dim] {user_input}\n\n"
                "[yellow]⚠  Agent orchestration not yet wired (coming in Phase 3).[/yellow]",
                border_style="yellow",
            )
        )
