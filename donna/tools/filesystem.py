"""
donna.tools.filesystem — File system tools (CRUD on the local hard drive).

These give the LLM the ability to navigate, read, write, and delete files
on the user's machine.  ``read_file`` and ``list_dir`` are **green** (safe);
``write_file`` and ``delete_file`` are **red** (require confirmation).
"""

from __future__ import annotations

import os
from pathlib import Path

from donna.tools.registry import tool


@tool(name="read_file", safety="green", description="Read the contents of a file.")
def read_file(path: str) -> str:
    """Read and return the full contents of the file at *path*."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"[ERROR] File not found: {target}"
    if not target.is_file():
        return f"[ERROR] Not a file: {target}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"[ERROR] Cannot read binary file as text: {target}"


@tool(name="list_dir", safety="green", description="List the contents of a directory.")
def list_dir(path: str = ".") -> str:
    """List files and directories inside *path* (defaults to cwd).

    Returns a formatted listing with [DIR] and [FILE] prefixes and sizes.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"[ERROR] Directory not found: {target}"
    if not target.is_dir():
        return f"[ERROR] Not a directory: {target}"

    lines: list[str] = [f"Contents of {target}:\n"]
    for entry in sorted(target.iterdir()):
        if entry.is_dir():
            lines.append(f"  [DIR]  {entry.name}/")
        else:
            size = entry.stat().st_size
            lines.append(f"  [FILE] {entry.name}  ({_human_size(size)})")
    return "\n".join(lines)


@tool(
    name="find_files",
    safety="green",
    description="Recursively find files matching a glob pattern (e.g. '*.py', '*.js').",
)
def find_files(pattern: str, path: str = ".") -> str:
    """Recursively search for files matching *pattern* under *path*.

    Parameters
    ----------
    pattern : str
        Glob pattern (e.g. ``"*.py"``, ``"*.txt"``, ``"test_*"``).
    path : str
        Root directory to search from (defaults to cwd).

    Returns a list of matching file paths, one per line.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"[ERROR] Directory not found: {target}"

    matches = sorted(target.rglob(pattern))
    # Filter out __pycache__, .git, and other noise
    matches = [
        m for m in matches
        if "__pycache__" not in str(m) and ".git" not in str(m)
    ]

    if not matches:
        return f"No files matching '{pattern}' found under {target}"

    lines = [f"Found {len(matches)} file(s) matching '{pattern}':\n"]
    for m in matches[:50]:  # Cap at 50 results
        lines.append(f"  {m.relative_to(target)}")
    if len(matches) > 50:
        lines.append(f"  ... and {len(matches) - 50} more")
    return "\n".join(lines)


@tool(
    name="write_file",
    safety="red",
    description="Write content to a file (creates or overwrites).",
)
def write_file(path: str, content: str) -> str:
    """Write *content* to *path*.  Creates parent directories if needed.

    ⚠️  This is a **red** tool — overwrites existing files.
    """
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"[OK] Written {len(content)} characters to {target}"


@tool(
    name="delete_file",
    safety="red",
    description="Delete a file from disk.",
)
def delete_file(path: str) -> str:
    """Delete the file at *path*.

    ⚠️  This is a **red** tool — deletion is irreversible.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"[ERROR] File not found: {target}"
    if not target.is_file():
        return f"[ERROR] Not a file (refusing to delete non-file): {target}"
    target.unlink()
    return f"[OK] Deleted {target}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _human_size(num_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.0f} {unit}"
        num_bytes /= 1024  # type: ignore[assignment]
    return f"{num_bytes:.1f} TB"
