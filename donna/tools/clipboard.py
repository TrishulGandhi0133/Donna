"""
donna.tools.clipboard — System clipboard read/write tools.

Uses ``pyperclip`` to interact with the OS clipboard.  This is what
powers the ``@fix`` and ``@explain`` shortcuts — the user copies an
error log or code snippet, then Donna reads it automatically.
"""

from __future__ import annotations

import pyperclip

from donna.tools.registry import tool


@tool(
    name="read_clipboard",
    safety="green",
    description="Read the current contents of the system clipboard.",
)
def read_clipboard() -> str:
    """Return whatever text is currently on the system clipboard.

    Returns ``"(clipboard is empty)"`` if nothing is copied.
    """
    try:
        content = pyperclip.paste()
        return content if content else "(clipboard is empty)"
    except pyperclip.PyperclipException as exc:
        return f"[ERROR] Clipboard access failed: {exc}"


@tool(
    name="write_clipboard",
    safety="green",
    description="Copy text to the system clipboard.",
)
def write_clipboard(text: str) -> str:
    """Copy *text* to the system clipboard.

    This is green because writing to clipboard is non-destructive;
    the user can always paste elsewhere.
    """
    try:
        pyperclip.copy(text)
        return f"[OK] Copied {len(text)} characters to clipboard."
    except pyperclip.PyperclipException as exc:
        return f"[ERROR] Clipboard access failed: {exc}"
