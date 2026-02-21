"""
donna.system.fingerprint — System discovery module.

Probes the user's machine on startup to detect installed tools,
OS details, and environment info.  The fingerprint is injected into
every agent's system prompt so the LLM knows what's available.

Cached per session — probes run once, not on every message.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from functools import lru_cache


# Tools to probe: (display_name, command)
_TOOL_PROBES: list[tuple[str, list[str]]] = [
    ("Python",  [sys.executable, "--version"]),
    ("Conda",   ["conda", "--version"]),
    ("Git",     ["git", "--version"]),
    ("Node",    ["node", "--version"]),
    ("npm",     ["npm", "--version"]),
    ("Docker",  ["docker", "--version"]),
    ("pip",     ["pip", "--version"]),
    ("Poetry",  ["poetry", "--version"]),
    ("Java",    ["java", "-version"]),
    ("Rust",    ["rustc", "--version"]),
]


def _probe_tool(command: list[str]) -> str | None:
    """Run a command and return the first line of output, or None if not found."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
        output = (result.stdout or result.stderr).strip()
        # Return just the first line (version info)
        return output.split("\n")[0].strip() if output else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


@dataclass
class SystemFingerprint:
    """Snapshot of the user's system environment."""

    os_name: str = ""
    os_version: str = ""
    hostname: str = ""
    username: str = ""
    home_dir: str = ""
    cwd: str = ""
    shell: str = ""
    installed_tools: dict[str, str] = field(default_factory=dict)
    missing_tools: list[str] = field(default_factory=list)

    @classmethod
    def detect(cls) -> SystemFingerprint:
        """Probe the system and return a populated fingerprint."""
        fp = cls()

        # --- OS & user info ---
        fp.os_name = f"{platform.system()} {platform.release()}"
        fp.os_version = platform.version()
        fp.hostname = platform.node()
        fp.username = os.getenv("USERNAME", os.getenv("USER", "unknown"))
        fp.home_dir = os.path.expanduser("~")
        fp.cwd = os.getcwd()

        if platform.system() == "Windows":
            fp.shell = "PowerShell"
        else:
            fp.shell = os.getenv("SHELL", "/bin/bash")

        # --- Probe tools ---
        for name, cmd in _TOOL_PROBES:
            version = _probe_tool(cmd)
            if version:
                fp.installed_tools[name] = version
            else:
                fp.missing_tools.append(name)

        return fp

    def to_prompt_section(self) -> str:
        """Format the fingerprint as a system-prompt injection block."""
        lines = [
            "## System Environment (auto-detected)",
            f"- OS: {self.os_name}",
            f"- OS Version: {self.os_version}",
            f"- Host: {self.hostname}",
            f"- User: {self.username}",
            f"- Home: {self.home_dir}",
            f"- CWD: {self.cwd}",
            f"- Shell: {self.shell}",
            "",
            "### Installed Tools",
        ]

        for name, version in self.installed_tools.items():
            lines.append(f"- ✅ {name}: {version}")

        if self.missing_tools:
            lines.append("")
            lines.append("### NOT Installed (do not use these)")
            for name in self.missing_tools:
                lines.append(f"- ❌ {name}")

        return "\n".join(lines)


@lru_cache(maxsize=1)
def get_fingerprint() -> SystemFingerprint:
    """Return a cached fingerprint (probes run once per session)."""
    return SystemFingerprint.detect()
