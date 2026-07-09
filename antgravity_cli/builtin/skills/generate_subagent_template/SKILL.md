---
name: "generate_subagent_template"
description: "Generates the structure and template files to create new modular subagents in the project."
---

# Skill: Generate Subagent Template (`generate_subagent_template`)

This skill is designed to guide and automate the creation of new modular subagents in the project, ensuring consistency in the file structure.

## Activation and Execution Instructions
Whenever the user requests the creation of a new subagent, for example with a prompt like "create a subagent to analyze logs" or explicitly "/generate_subagent_template <subagent_name>":

1. **Identify the Name**:
   - If the user specified the name of the subagent, normalize it to snake_case or kebab-case (e.g., `log_analyzer`).
   - If the name was not provided, ask the user for it in a text response. Do not execute any commands until you have a valid subagent name.
2. **Execute the Automation**:
   - First, find the absolute path of `generate_subagent.py`. You can use `FIND_FILE` or `SEARCH_DIR` to search for it (it resides inside the `antgravity_cli` folder under `builtin/skills/generate_subagent_template/scripts/`).
   - Run the script with Python using the `RUN_COMMAND` tool:
     ```powershell
     python <absolute_path_to_generate_subagent.py> <subagent_name>
     ```
3. **Explain the Structure**: After successful creation, explain to the user what each part of the new modular structure does:
   - **`AGENT.md`**: Defines name, description, capabilities, and the system instructions (prompt) for the subagent.
   - **`scripts/`**: Directory for the subagent's custom tools/skills.
   - **`references/`**: Directory for supporting documentation.
