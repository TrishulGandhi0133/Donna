# DONNA: Digital Operative for Non-Negotiable Automation

**Version:** 1.0.0 (The "It Works On My Machine" Release)  
**Status:** Local-First, Privacy-Obsessed, Judgmental.

---

## 1. Executive Summary

Donna is not a chatbot. Chatbots are for people who like browser tabs. Donna is a CLI-resident, multi-agent framework that lives in your terminal, has full system access, and learns from its own incompetence.

It is designed on a "Local-First" philosophy. It utilizes your local hardware (or API keys if you must) to act as an operating system layer between your intent and the command line. It features a unique "Grudge-Holding" memory architecture (Feedback Loops) and passive observation capabilities.

---

## 2. Core Architecture

The system is built as a modular Python library wrapping a Model-Agnostic Backend.

### 2.1 The "Body" (Infrastructure)
* **Interface:** Pure CLI. No electron apps, no web UIs. Speed is the only metric.
* **I/O:** Multimodal support.
    * *Input:* Text (stdin), Images (file paths), Clipboard content.
    * *Output:* Stdout, File operations, System signals.
* **Model Layer:**
    * **Primary:** Ollama (Local Llama 3, Mistral) for privacy and speed.
    * **Cloud Fallback:** Groq API (for when you need speed over privacy).
* **Tooling Layer:** A registry of Python functions (`@tool` decorators) that agents can invoke.

### 2.2 The "Staff" (Agent Configuration)
Donna is not a monolith. She is a trench coat containing three raccoons. You define specific agents in a `config.yaml` file:

* **@router:** The lightweight dispatcher. Routes prompts to the correct specialist.
* **@coder:** specialized in syntax, debugging, and git.
* **@sysadmin:** Has elevated privileges (careful with this one).
* **@critic:** The internal auditor. Reviews output before it hits your screen.

---

## 3. Detailed Feature Specifications

### 3.1 The "Grudge" Memory System (Feedback Loop)
Most AIs have the memory of a goldfish. Donna has a file.

* **Logic:** When an agent fails or produces suboptimal code, the user provides a correction.
* **Storage:** This correction is appended to `feedback.md` in the agent's specific directory.
* **Retrieval:** Before *every* subsequent generation, the agent reads its specific `feedback.md`.
* **Effect:** It effectively performs "Manual RLHF" (Reinforcement Learning from Human Feedback). If you tell it once "Don't use `pip`, use `poetry`", it will statistically lower the probability of suggesting `pip` in the future.

### 3.2 Semantic Clipboard (@fix)
Stop copy-pasting error logs like a caveman.

* **Workflow:**
    1.  User copies a stack trace or code snippet in any window.
    2.  User types `@fix` or `@explain` in the Donna CLI.
* **Backend Logic:**
    1.  Donna invokes `pyperclip` (or OS specific equivalent) to read the system clipboard buffer.
    2.  The clipboard content is injected into the System Prompt as `context_window`.
    3.  The LLM processes the request against the invisible context.

### 3.3 Watch & Learn (Imitation Learning)
Why write tools when you can just demonstrate them?

* **Command:** `@donna --watch`
* **The Workflow:**
    1.  **Recording State:** Donna hooks into the shell session (using `script` or `pty` wrappers).
    2.  **Action:** User performs a task (e.g., `git add .`, `git commit -m "wip"`, `git push origin dev`).
    3.  **Stop:** User types `stop`.
    4.  **Synthesis:** Donna sends the transcript (Input Commands + System Outputs) to the LLM.
    5.  **Generation:** The LLM generates a reusable Python script or shell alias for this sequence.
    6.  **Storage:** The new tool is saved to `~/.donna/skills/` and is immediately available.

### 3.4 Safety Protocols (Red/Green Tooling)
Since Donna has system access, we prevent accidental `rm -rf /`.

* **Green Tools (Read-Only):** `cat`, `ls`, `grep`, `curl`. (Executed automatically).
* **Red Tools (Write/Execute):** `rm`, `mv`, `write_file`, `exec_shell`.
* **The Interceptor:**
    * When the LLM predicts a Red Tool usage, the execution pauses.
    * CLI Output: `[ALERT] Agent @sysadmin wants to run: 'rm -rf ./temp'. Allow? [y/N]`
    * Default is always **No**.

---

## 4. End-to-End Workflows

### 4.1 The "Fix It" Loop
**User:** `@coder The build failed again.` (Clipboard contains error log)

1.  **Router:** Detects `@coder` tag.
2.  **Context Loading:**
    * Loads `coder_system_prompt.txt`.
    * Loads `feedback.md` (Recall: "User hates verbose comments").
    * Loads Clipboard content.
3.  **Thinking (ReAct):**
    * *Thought:* Error indicates missing dependency `numpy`.
    * *Action:* Check `requirements.txt`.
4.  **Tool Execution:** Reads file.
5.  **Synthesis:** *Thought:* `numpy` is missing.
6.  **Response:** "You forgot numpy again. I've drafted the pip install command. Run it?"

### 4.2 The "New Skill" Loop
**User:** `@donna I want to create a new React component automatically.`

1.  **Donna:** "I don't know how to do that. Show me? (Type --watch)"
2.  **User:** Runs `--watch`. Creates a folder, creates `index.js`, creates `style.css`. Stops.
3.  **Donna:** Analyzes the file creation patterns.
4.  **Generation:** Creates a new tool function `create_component(name)`.
5.  **Outcome:** Next time, user types `@donna create_component Header`, and the files appear instantly.

---

## 5. Technical Stack

* **Language:** Python 3.10+
* **Core Libraries:**
    * `langchain` or `swarms` (for orchestration).
    * `typer` or `click` (for the CLI interface).
    * `rich` (for pretty printing markdown/code in terminal).
    * `watchdog` (for filesystem triggers).
* **Data Store:**
    * `ChromaDB` (Local vector store for long-term memory).
    * `JSON/YAML` (Configuration).
    * `Markdown` (Feedback logs).


# Full System Access: The "God Mode" Protocol

**Component:** Core Backend Logic  
**Security Level:** Critical (Red)  
**Philosophy:** "Your Agent is a Superuser."

---

## 1. What Does "Full System Access" Actually Mean?

In most AI applications (like ChatGPT or Claude), the AI is **sandboxed**. It lives in a browser tab. It cannot see your desktop, it cannot read your files, and it definitely cannot install software. It is a brain in a jar.

**Full System Access** breaks the jar.

It means giving the AI agent the same permissions and capabilities as a **human system administrator** sitting at your keyboard. It treats the Operating System (Windows, macOS, Linux) not as a boundary, but as a toolset.

### The Mental Model
Imagine hiring a remote developer and giving them **SSH access** to your machine.
* They can navigate your folders.
* They can run scripts.
* They can install packages.
* They can fix bugs in your local environment.

**Donna is that remote developer.**

---

## 2. What Should It Do? (Functional Requirements)

To achieve this, the library must expose specific "OS Primitives" to the Large Language Model (LLM). The LLM doesn't just output text; it outputs **calls to these functions**.

### A. The Filesystem Hand (Read/Write/Manipulate)
The agent must be able to treat your hard drive as its own memory.

* **Navigation:** It must know "where" it is. (e.g., `cwd` - Current Working Directory).
* **CRUD Operations:**
    * **Create:** Generate new code files, config files, or documentation (`main.py`, `.env`).
    * **Read:** Open and analyze error logs, existing codebases, or data files (`error.log`).
    * **Update:** Patch specific lines of code to fix bugs without rewriting the whole file.
    * **Delete:** Remove temporary files or cleanup garbage (Requires strict permission).

### B. The Terminal Hand (Shell Execution)
This is the most powerful capability. The agent uses the Command Line Interface (CLI) to interact with the kernel.

* **Package Management:** `pip install`, `npm install`, `brew install`.
* **Version Control:** `git commit`, `git push`, `git checkout`.
* **Process Control:** Start servers (`npm start`), run scripts (`python app.py`), or kill frozen apps.
* **System Config:** Change display settings, network configurations, or environment variables.

### C. The Application Hand (Inter-Process Communication)
The agent should control other software running on the machine.

* **Launch:** Open VS Code, Spotify, or Chrome.
* **Clipboard:** Read what you just copied (`Ctrl+C`) and paste answers (`Ctrl+V`).
* **Screenshots:** "Look" at the screen to debug UI issues (if using multimodal models).

---

## 3. The Implementation Logic (The "How")

### The Loop
1.  **User Intent:** "Fix the bug in the server."
2.  **Agent Thought:** "I need to see the error log."
3.  **Tool Call:** `read_file("./server.log")`
4.  **System Output:** (Returns the last 50 lines of the log).
5.  **Agent Thought:** "It's a missing library. I need to install it."
6.  **Tool Call:** `execute_shell("pip install flask")`
7.  **System Output:** "Successfully installed."

### The "Safety Valve" (Crucial)
Because this is dangerous, you **must** implement a `Human-in-the-Loop` middleware.

* **Green Actions (Safe):** `ls`, `cat`, `echo`, `grep`. -> **Auto-Execute.**
* **Red Actions (Dangerous):** `rm`, `mv`, `sudo`, `> (overwrite)`. -> **Pause for Confirmation.**

> **Donna CLI:**
> ⚠️ **Agent @sysadmin wants to run:** `rm -rf ./project_folder`
> **Allow? [y/N]:**

---

## 4. Use Case Scenarios

| Scenario | Standard AI | Donna (Full Access) |
| :--- | :--- | :--- |
| **"I have a Python error."** | Explains the error. You have to copy-paste the fix. | Reads the file, applies the patch, runs the script to verify the fix. |
| **"Organize my downloads."** | Gives you a checklist of how to do it. | Scans `~/Downloads`, creates folders (Images, PDFs), and moves files automatically. |
| **"Set up a React app."** | Gives you a tutorial. | Runs `npx create-react-app`, installs dependencies, and opens VS Code for you. |

---

**Summary:** Full System Access turns the AI from a **Consultant** (who gives advice) into a **Worker** (who does the job).