# AntGravity CLI

<p align="center">
  <img src=".img/ant%20gravity.png" alt="AntGravity CLI Logo" width="400">
</p>

A portable and interactive command-line interface (CLI) developed in Python to flexibly interact with agents from the **Google Antigravity** ecosystem.

---

## Requirements

- Python 3.11+
- Installed dependencies (including `google-antigravity`, `click`, `colorama`, `python-dotenv`, `rich`, `prompt-toolkit`, and `PyYAML`).

---

## Installation and Setup

### Global Installation (via PyPI)
Install the package globally or in your virtual environment:
```powershell
pip install AntGravityCLI
```
Once installed, you can run the CLI from anywhere using:
```powershell
antgravity [options] [prompt]
# or the shortcut alias:
ant [options] [prompt]
```

### Development Setup
1. Clone the repository and navigate to the project folder.
2. Make sure the virtual environment is activated:
   ```powershell
   .\.venv\Scripts\activate
   ```
3. Install package dependencies in editable mode:
   ```powershell
   pip install -e .
   ```
4. Configure your environment using a `.env` file by copying the template:
   ```powershell
   cp .env.example .env
   ```

### Running the Test Suite
The test suite has been restructured into a modular `tests/` package. To run all tests and check for regressions, execute:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Interactive Workspace Setup (`init` command)
To initialize a new project workspace with the required folders (`.agents/`, `.agents/skills/`, `.agents/subagents/`), templates, and a configured `.env` file, run the click-native `init` subcommand:
```powershell
ant init
# or with language options (e.g., pt-br)
ant init --language pt-br
```

---

## Environment Resolution and Default Values

The CLI resolves configuration by loading `.env` files. By default, it loads them in two stages:
1. **Physical CLI script installation folder**: Loads `.env` for global default configuration.
2. **Current Working Directory (CWD)**: Loads `.env` for workspace-specific configurations (which override the global ones).

Alternatively, you can load a custom `.env` file using the `--env-file` / `-e` option. When a custom `.env` file is specified, the default `.env` files (global and CWD) are **not** loaded automatically, giving you full control over the variables.

If a `.env` file is not present or a specific variable is not set, the CLI falls back to the following default values:

| Environment Variable | CLI Option | Description | Default Value |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | `--api-key` | Gemini API Key | *None (Required)* |
| `GEMINI_MODEL` | `--model` / `-m` | Gemini Model to be used | `gemini-3.1-flash-lite` |
| `ANTGRAVITY_LANG` | `--language` / `-l` | CLI UI Language | `en-us` |
| `ANTGRAVITY_YOLO` | `--yolo` / `-y` | Run in YOLO (Safe-bypass) Mode | `False` (Safe Mode) |
| `ANTGRAVITY_WORKSPACE` | `--workspace` / `-w` | Restricted workspace paths | *None (Current CWD)* |
| `ANTGRAVITY_SYSTEM_INSTRUCTION` | `--system-instruction` / `-s` | System instruction or path | *None* |
| `ANTGRAVITY_SKILLS_PATH` | `--skills-path` / `-k` | Custom workspace skills folders | *None* |
| `ANTGRAVITY_SILENT` | `--silent` | Hide thoughts and tool execution logs | `False` |
| `ANTGRAVITY_VERBOSE` | `--verbose` / `-v` | Show internal reasoning details | `False` |
| `ANTGRAVITY_VERBOSE_SUBAGENTS` | `--verbose-subagents` | Show internal reasoning details for subagents | `False` |

*(You can always override these values dynamically by passing their respective flags on the command line).*

---

## How to Use

### 1. Single Prompt Mode
To send a prompt and receive the response directly:
```powershell
ant "Write a greeting in Python"
```

### 2. Interactive Mode (REPL)
To start a continuous chat with the agent (which maintains session history):
```powershell
ant
```
**Useful commands in Interactive Mode:**
- `/reset`: Clears conversation history and resets agent context.
- `/exit` or `/quit`: Closes the interactive terminal.
- `/help` or `?`: Displays a detailed help message with all commands, active skills, and subagents.
- `/ants` or `/subagents`: Lists all registered colony subagents and their capabilities.
- `/disable_skill <name>`: Disables a global skill in the active session.
- `/enable_skill <name>`: Re-enables a previously disabled global skill.
- `/disable_agent <name>`: Disables a colony subagent (blocking delegation to it).
- `/enable_agent <name>`: Re-enables a previously disabled colony subagent.

**Auto-completion and Interactive Features:**
* **Platform-Standard History Location**: Command history is automatically saved to platform-compliant directory paths instead of user home cluttering:
  - **Windows**: `%LOCALAPPDATA%\AntGravity\history`
  - **macOS**: `~/Library/Application Support/AntGravity/history`
  - **Linux**: `~/.local/share/antgravity/history`
* **Active Agent Prompt Indicator**: When a subagent is executing or was invoked, the prompt dynamically updates (e.g. `You (-> SubagentName) >` or `Você (-> SubagentName) >`) to show you the current agentic context.
* **Real-time Auto-completion**: Typing `/` triggers commands/skills, `@` triggers workspace files, and `:` lists colony subagents. Auto-completion features substring/middle-of-path matching, prefix prioritization, case-insensitivity, and backspace stability.
* **Smart Ellipsis for Skills**: At REPL startup, active skills are listed in the welcome banner up to a limit of 5. Any excess skills are summarized with a localized ellipsis (`... and more` or `... e mais`).

### 3. Safe Mode vs YOLO Mode
- **Safe Mode (Default)**: Whenever the agent tries to run risky terminal commands (like the `RUN_COMMAND` tool), the CLI will request your permission in the console (`[y/N]`) before proceeding.
- **YOLO Mode (`-y` / `--yolo`)**: Disables all safety confirmations and executes all actions autonomously.
  ```powershell
  ant -y "Create a folder named test and list the directory"
  ```

---

## Available Options

You can customize the CLI behavior using flags:

| Flag | Shortcut | Env Variable | Description |
| :--- | :--- | :--- | :--- |
| `--model` | `-m` | `GEMINI_MODEL` | Specifies the Gemini model (default: `gemini-3.1-flash-lite`). |
| `--yolo` | `-y` | `ANTGRAVITY_YOLO` | Skips all permissions/confirmations and runs everything freely. |
| `--workspace` | `-w` | `ANTGRAVITY_WORKSPACE` | Restricts file tools to a specific directory (can be repeated). |
| `--system-instruction` | `-s` | `ANTGRAVITY_SYSTEM_INSTRUCTION` | Text with custom system instructions or path to a text file. |
| `--api-key` | | `GEMINI_API_KEY` | Passes the API key directly on the command line. |
| `--skills-path` | `-k` | `ANTGRAVITY_SKILLS_PATH` | Path to skills folders (can be repeated). |
| `--silent` | | `ANTGRAVITY_SILENT` | Hides internal thoughts and tool calls in the terminal. |
| `--verbose` | `-v` | `ANTGRAVITY_VERBOSE` | Displays the AI's internal reasoning thoughts in gray. |
| `--verbose-subagents` | | `ANTGRAVITY_VERBOSE_SUBAGENTS` | Displays internal reasoning thoughts and tool execution logs for subagents, prefixed with `[SubagentName]`. |
| `--language` | `-l` | `ANTGRAVITY_LANG` | Specifies the output translation language (default: `en-us`). |
| `--env-file` | `-e` | | Path to a custom `.env` file to load configurations from. |
| `--version` | `-V` | | Displays the installed CLI version. |

---

## Localization (i18n)

The AntGravity CLI features built-in internationalization (i18n). Output messages, error states, and terminal prompts are decoupled from the source code and stored as JSON translation files inside the `translate/` directory.

### Structure of `translate/`
```text
translate/
├── pt-br/                         # Brazilian Portuguese translations
│   ├── config.json
│   ├── console_io.json
│   ├── handlers.json
│   ├── parser.json
│   ├── repl.json
│   ├── runner.json
│   └── commands.json
└── en-us/                         # English translations (Default)
    ├── config.json
    ├── console_io.json
    ├── handlers.json
    ├── parser.json
    ├── repl.json
    ├── runner.json
    └── commands.json
```

### Adding New Languages
To support a new language (e.g. `es-es` for Spanish):
1. Create a new directory named after the locale code inside `translate/` (e.g. `translate/es-es/`).
2. Copy the JSON files from `translate/en-us/` into the new folder and translate their text values.
3. Switch the CLI runtime language using the `--language es-es` flag.

---

## Customization and Settings (`.agents`)

The `.agents` folder at the root of your project is the **Local Workspace Customization** folder. Through it, you can define rules, create new skills, and customize agent responses.

### Complete Structure of `.agents`

```text
my-project/
└── .agents/
    ├── AGENTS.md                  # Project rules and guidelines
    ├── skills/                    # Folder containing specific skills
    │   └── my_custom_skill/       # Example of a skill
    │       ├── SKILL.md           # Skill instructions and triggers (Required)
    │       ├── scripts/           # Supporting scripts
    │       ├── examples/          # Usage/code examples
    │       └── references/        # Reference documentation
    └── subagents/                 # Colony subagents folder
        └── my_subagent/
            ├── AGENT.md           # Subagent manifesto and instructions
            └── scripts/           # Custom python/shell tools
```

### 1. Project Rules (`AGENTS.md`)
The `.agents/AGENTS.md` file defines the general rules of behavior, style, and technical constraints that the agent must follow in this project.
*Global rules can be set at `C:\Users\<user>\.gemini\config\AGENTS.md` for machine-wide application.*

### 2. Skills (`skills/`)
Skills are packages of behavior dynamically loaded depending on context.
*   **The `SKILL.md` file (Required)**: Defines name, description YAML frontmatter and the body with instructions.
*   **Scripts (`scripts/`)**: Executable scripts inside are automatically exposed as tools (e.g., `my_custom_skill.script_name`).

### 3. Subagents (`subagents/`)
Subagents are specialized workers configured to execute isolated tasks under the parent agent's delegation.
* **The `AGENT.md` file (Required)**: Defines configuration frontmatter and system instructions. YAML parsing is powered by native Python `PyYAML` integration.
* **Custom Tools (`scripts/`)**: Scripts inside automatically register as subagent-exclusive tools.
