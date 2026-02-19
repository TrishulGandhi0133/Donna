# Donna — Digital Operative for Non-Negotiable Automation

> A CLI-resident, multi-agent framework that lives in your terminal, has full system access, and learns from its own incompetence.

---

## Quick Start

### 1. Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Ollama** (optional, for local models) — [ollama.com](https://ollama.com/)
- **Groq API key** (optional, for cloud models) — [console.groq.com](https://console.groq.com/)

### 2. Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/Donna.git
cd Donna

# Install in editable mode (development)
pip install -e ".[dev]"
```

Or install directly from the repo:

```bash
pip install git+https://github.com/YOUR_USERNAME/Donna.git
```

### 3. Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your GROQ_API_KEY (if using cloud mode)
```

The main config lives in `config/config.yaml`. Edit it to change models, agents, safety rules, etc.

### 4. Run

```bash
# Check installation
donna --version

# View current config
donna info

# Start interactive chat
donna chat

# Use Groq cloud model instead of Ollama
donna chat --cloud

# One-shot prompt
donna run "list all Python files in this directory"

# Give feedback to an agent
donna feedback "always use poetry, not pip" --agent coder
```

---

## Project Structure

```
Donna/
├── donna/                  # Python package
│   ├── cli.py              # Typer CLI entry-point
│   ├── shell.py            # Interactive REPL (prompt_toolkit + rich)
│   ├── config.py           # Config loader (Pydantic + YAML)
│   ├── agents/             # Agent definitions (Phase 3)
│   ├── tools/              # Tool registry & built-ins (Phase 2)
│   ├── models/             # LLM backends — Ollama & Groq (Phase 2)
│   ├── memory/             # Grudge memory + ChromaDB (Phase 3)
│   ├── safety/             # Red/Green interceptor (Phase 3)
│   ├── watch/              # Watch & Learn recorder (Phase 4)
│   └── skills/             # Auto-generated skills (Phase 4)
├── config/
│   ├── config.yaml         # Main configuration
│   └── prompts/            # System prompts per agent
├── tests/                  # Test suite
├── pyproject.toml          # Package metadata & dependencies
└── README.md
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check donna/
```

---

## License

MIT
