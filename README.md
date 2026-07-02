# AntGravity CLI

A portable and interactive command-line interface (CLI) developed in Python to flexibly interact with agents from the **Google Antigravity** ecosystem.

## Requirements

- Python 3.11.7 (as configured in the development environment).
- Installed dependencies (including `google-antigravity`, `click`, `colorama`, `python-dotenv`).

## Installation and Setup

1. Make sure the virtual environment is activated:
   ```powershell
   .\.venv\Scripts\activate
   ```
2. Set the Gemini API key by creating a `.env` file at the root of the project:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   *(Or pass it via the `--api-key` flag during executions).*

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

### 3. Safe Mode vs YOLO Mode
- **Safe Mode (Default)**: Whenever the agent tries to run risky terminal commands (like the `RUN_COMMAND` tool), the CLI will request your permission in the console (`[y/N]`) before proceeding.
- **YOLO Mode (`-y` / `--yolo`)**: Disables all safety confirmations and executes all actions autonomously.
  ```powershell
  python main.py -y "Create a folder named test and list the directory"
  ```

---

## Available Options

You can customize the CLI behavior using flags:

| Flag | Shortcut | Description |
| :--- | :--- | :--- |
| `--model` | `-m` | Specifies the Gemini model (default: `gemini-3.5-flash`). |
| `--yolo` | `-y` | Skips all permissions/confirmations and runs everything freely. |
| `--workspace` | `-w` | Restricts file tools to a specific directory (can be repeated). |
| `--system-instruction` | `-s` | Text with custom system instructions or path to a text file. |
| `--api-key` | | Passes the API key directly on the command line. |
| `--skills-path` | `-k` | Path to skills folders (can be repeated). If not provided and the `./skills` folder exists, it will be loaded by default. |
| `--silent` | | Hides internal thoughts and tool calls in the terminal. |
| `--verbose` | `-v` | Displays the AI's internal reasoning thoughts (Chain of Thought) in gray on the console. |

Advanced usage example:
```powershell
python main.py -m gemini-3.5-flash -y -s "You are a concise assistant speaking Spanish" "Hello!"
```

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
        └── gerenciar_deploy/      # Example of a skill
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
    Any executable script inserted in the `scripts/` folder will be automatically exposed as a tool that the agent can run (e.g., `gerenciar_deploy.script_name`).

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
