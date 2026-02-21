# Donna — Your AI DevOps Agent in the Terminal

> **pip install donna-cli** → **donna setup** → done. Your personal AI agent that runs commands, manages files, and automates developer workflows — right from your terminal.

---

## ⚡ 30-Second Setup

```bash
pip install donna-cli
donna setup
donna chat --cloud
```

That's it. `donna setup` asks for your **Groq API key** (free at [console.groq.com](https://console.groq.com/keys)) and you're ready to go.

---

## What Can Donna Do?

```bash
# System info
donna run "what's my system spec?" --cloud

# File operations
donna run "find all Python files in this project" --cloud

# Environment setup
donna run "create a conda env called ml with python 3.11 and install numpy" --cloud

# Project scaffolding
donna run "scaffold a Flask project with routes and tests" --cloud

# DevOps / Admin
donna run "show disk space and running processes" --cloud
```

### Interactive Mode

```bash
donna chat --cloud     # Cloud mode (Groq — fast, free)
donna chat             # Local mode (Ollama — private, offline)
```

---

## Why Donna?

| | ChatGPT | Cursor | **Donna** |
|---|---------|--------|-----------|
| Your data | Goes to cloud | Goes to cloud | **Stays on your machine** |
| System access | None | File edits only | **Full shell, files, processes** |
| Runs where | Browser | IDE | **Terminal, SSH, servers** |
| Remembers you | Per-session | Per-session | **Persistent memory** |
| Learns corrections | No | No | **Yes** |

---

## Features

- 🧠 **Multi-agent routing** — `@coder` for code tasks, `@sysadmin` for system ops
- 🔒 **Safety gate** — destructive commands ask `Allow? [y/N]` before running
- 📋 **Task planner** — generates a step-by-step plan before complex tasks
- 🔍 **System fingerprint** — auto-detects installed tools (Git, Conda, Node, Docker...)
- 💾 **Grudge memory** — `donna feedback "always use poetry"` — remembers forever
- 🏠 **Local-first** — works with Ollama for 100% offline, private usage
- ☁️ **Cloud fallback** — switch to Groq for faster responses with `--cloud`

---

## Commands

```bash
donna setup              # First-time config (Groq key, Ollama model)
donna setup --reset      # Reconfigure

donna chat               # Interactive chat (local Ollama)
donna chat --cloud       # Interactive chat (Groq cloud)
donna chat --agent coder # Pin to a specific agent

donna run "prompt" --cloud  # One-shot execution
donna info                  # Show current config

donna feedback "correction" --agent coder   # Teach Donna
donna feedback --list --agent coder         # View feedback
```

---

## Requirements

- **Python 3.10+**
- One of:
  - **Groq API key** (free) — for cloud mode
  - **Ollama** ([ollama.com](https://ollama.com/)) — for local mode

---

## Development

```bash
git clone https://github.com/TrishulGandhi0133/Donna.git
cd Donna
pip install -e ".[dev]"
pytest tests/ -v    # 78 tests
```

---

## License

MIT
