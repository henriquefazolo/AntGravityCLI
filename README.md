# AntGravity CLI

<p align="center">
  <img src=".img/ant%20gravity.png" alt="AntGravity CLI Logo" width="400">
</p>

A portable and interactive command-line interface (CLI) developed in Python to flexibly interact with agents from the **Google Antigravity** ecosystem.

## Requirements

- Python 3.11.7 (as configured in the development environment).
- Installed dependencies (including `google-antigravity`, `click`, `colorama`, `python-dotenv`).

## Installation and Setup

1. Make sure the virtual environment is activated:
   ```powershell
   .\.venv\Scripts\activate
   ```
2. Configure your environment using a `.env` file. You can copy the template from [.env.example](file:///.env.example) to get started:
   ```powershell
   cp .env.example .env
   ```

### Environment Resolution and Default Values

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

*(You can always override these values dynamically by passing their respective flags on the command line).*


---

## How to Use

### 1. Single Prompt Mode
To send a prompt and receive the response directly:
```powershell
python main.py "Write a greeting in Python"
```

### 2. Interactive Mode (REPL)
To start a continuous chat with the agent (which maintains session history):
```powershell
python main.py
```
**Useful commands in Interactive Mode:**
- `/reset`: Clears conversation history and resets agent context.
- `/exit` or `/quit`: Closes the interactive terminal.

**Auto-completion and Active Skills:**
* **Real-time Auto-completion**: As you type `/` in the prompt (either at the start or mid-sentence), a dynamic dropdown menu displaying all special commands and active skills will instantly pop up. Similarly, typing `@` triggers dynamic file and folder suggestions from your workspace repository (ignoring folders like `.git`, `.venv`, etc.). The autocomplete supports middle-of-path/substring matching, prioritizes exact prefix matches, is case-insensitive, stays open stably when you delete characters (Backspace), and ignores regular chat text and trailing spaces to maintain a clean console.
* **Banner Skills Listing**: At REPL startup, a welcome banner displays all available active workspace skills one per line, limited to 5. If more than 5 exist, a localized ellipsis (`... and more` or `... e mais`) is appended.
* **Hybrid Skills Resolution**: By default (when `--skills-path` / `-k` is not specified), the welcome banner list, autocomplete menu, and prompt parser strictly load active skills from the CLI script's physical installation directory (`.agents/skills`), even when executing the CLI from or targeting a different CWD/workspace. This ensures that internal CLI utility skills (like `/generate_skill_template`) are always loaded and executable. If you explicitly pass one or more custom paths via the `--skills-path` / `-k` flag, the CLI dynamically loads **both** your custom/local workspace skills and the physical Ant installation skills simultaneously, giving you access to both sets of tools in the REPL session.

### 3. Safe Mode vs YOLO Mode
- **Safe Mode (Default)**: Whenever the agent tries to run risky terminal commands (like the `RUN_COMMAND` tool), the CLI will request your permission in the console (`[y/N]`) before proceeding.
- **YOLO Mode (`-y` / `--yolo`)**: Disables all safety confirmations and executes all actions autonomously.
  ```powershell
  python main.py -y "Create a folder named test and list the directory"
  ```

### 4. Listing Available Skills
You can quickly scan and list the names of all active local agent skills folders registered in `.agents/skills/` using the utility script:
```powershell
python list_skills.py
```
*(This script supports localization, reading the system language from the `ANTGRAVITY_LANG` environment variable).*

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
| `--skills-path` | `-k` | `ANTGRAVITY_SKILLS_PATH` | Path to skills folders (can be repeated). If not provided and the `./skills` folder exists, it will be loaded by default. |
| `--silent` | | `ANTGRAVITY_SILENT` | Hides internal thoughts and tool calls in the terminal. |
| `--verbose` | `-v` | `ANTGRAVITY_VERBOSE` | Displays the AI's internal reasoning thoughts (Chain of Thought) in gray on the console. |
| `--language` | `-l` | `ANTGRAVITY_LANG` | Specifies the output translation language (default: `en-us`, e.g. `pt-br`, `en-us`). |
| `--env-file` | `-e` | | Path to a custom `.env` file to load configurations from (bypasses default global and local .env files). |

Advanced usage example:
```powershell
python main.py -m gemini-3.5-flash -y -s "You are a concise assistant speaking Spanish" "Hello!"
```

---

## Localization (i18n)

The AntGravity CLI features built-in internationalization (i18n). Output messages, error states, and terminal prompts are decoupled from the core source code and stored as localized translation files inside the `translate/` directory.

### Structure of `translate/`
```text
translate/
├── pt-br/                         # Brazilian Portuguese translations
│   ├── config.json
│   ├── console_io.json
│   ├── handlers.json
│   ├── parser.json
│   └── repl.json
└── en-us/                         # English translations (Default)
    ├── config.json
    ├── console_io.json
    ├── handlers.json
    ├── parser.json
    └── repl.json
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
    ├── skills.json                # (Optional) Skills configuration and registration
    └── skills/                    # Folder containing specific skills
        └── my_custom_skill/       # Example of a skill
            ├── SKILL.md           # Skill instructions and triggers (Required)
            ├── scripts/           # Supporting scripts
            ├── examples/          # Usage/code examples
            └── references/        # Reference documentation
```

### 1. Project Rules (`AGENTS.md`)
The `.agents/AGENTS.md` file defines the general rules of behavior, style, and technical constraints that the agent must follow in this project (e.g., code pattern, language, preferred frameworks).

*There is also the global scope at `C:\Users\<user>\.gemini\config\AGENTS.md` for rules that apply to the entire machine.*

### 2. Skills (`skills/`)
**Skills** are packages of behavior and tools dynamically loaded depending on conversation context or user request.

*   **The `SKILL.md` file (Required)**:
    Defines YAML metadata (used by the AI for auto-activation) and the body with the skill instructions:
    ```markdown
    ---
    name: "Utility Development Tools"
    description: "Useful for any general development, automation, scripting, or workspace query task."
    ---

    # Skill Instructions
    Whenever the user requests an automation or script execution:
    1. Analyze the prompt and use the corresponding tools in `scripts/`.
    2. Explain the execution result at the end.
    ```
*   **Scripts (`scripts/`)**:
    Any executable script inserted in the `scripts/` folder will be automatically exposed as a tool that the agent can run (e.g., `my_custom_skill.script_name`).

### 3. Skills Registration (`skills.json`)
The `skills.json` file at the root of the `.agents/` folder allows inheriting skills from other shared directories or disabling default skills:
```json
{
  "entries": [
    { "path": "path/to/external/skills" }
  ],
  "exclude": [
    "skill_name_to_ignore"
  ]
}
```

### 4. Subagents (`subagents/`)
**Subagents** (or helper ants) are specialized secondary agents configured to execute isolated tasks under the parent agent's delegation. They are declared in a modular folder structure:
* **Directory Structure**: `.agents/subagents/<subagent_name>/`
  ```text
  .agents/subagents/log_analyzer/
  ├── AGENT.md            # Subagent config (YAML) and system instructions (Required)
  ├── scripts/            # Python/Shell scripts acting as the subagent's custom tools/skills
  └── references/         # Supporting documentation or references for this subagent
  ```

* **The `AGENT.md` file (Required)**: Defines the subagent configuration using YAML frontmatter, and the body contains the system instructions for this subagent:
  ```markdown
  ---
  name: "LogAnalyzer"
  description: "Specialist in analyzing logs and reporting errors."
  capabilities:
    enabled_tools:
      - VIEW_FILE
  tools:
    - read_log_metadata
  ---

  # Subagent Instructions
  You are a subagent specialized in reading logs. Find errors and format them in markdown tables.
  ```

* **The Concept of "Subagent Skills"**:
  Unlike the main agent, subagents do **not** require internal `skills/` directories containing `SKILL.md` files. Conceptually, a subagent itself *is* a self-contained specialist.
  * **System Instructions (`AGENT.md`)**: The body of this file functions like the `SKILL.md` instructions, defining how the subagent should act.
  * **Custom Tools (`scripts/`)**: Any script placed inside the subagent's `scripts/` folder automatically acts as its exclusive "skills" or custom tools (registered under `tools:` in its frontmatter). These are executed by the parent runner on the subagent's behalf.

#### How Subagents are Invoked
The parent agent automatically delegates complex tasks to registered subagents using the built-in `start_subagent` tool.
* **Tool Call Parameters**:
  * You will see log updates like `[Tool] Calling: start_subagent with {}` in the console.
  * The `{}` represents the tool execution arguments. If it is empty, it means no custom prompts or parameters are passed, so the subagent runs using its default system instructions defined in `AGENT.md` (which is standard for simple task delegation).
  * For more complex operations, the parent agent can pass parameters like `"agent_name"` or `"prompt"` inside this block.

---

## Agent Personality and Instructions

The agent's personality, tone of voice, and behavioral guidelines are resolved at multiple levels of precedence:

1. **Initialization Flag (`-s` / `--system-instruction`)**:
   Defines system instructions directly in command execution (free text or file path).
2. **Local and Global Rules (`AGENTS.md`)**:
   Read from `.agents/AGENTS.md` (local) and `C:\Users\<user>\.gemini\config\AGENTS.md` (global).
3. **Skill Instructions (`SKILL.md`)**:
   Merged into the chat context when the corresponding skill is activated.
4. **Default Personality (Fallback)**:
   If no instruction is provided, assumes the default profile of the Google Antigravity ecosystem.
