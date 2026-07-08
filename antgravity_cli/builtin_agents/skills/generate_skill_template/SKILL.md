---
name: "generate_skill_template"
description: "Generates the structure and template files to create new skills in the project."
---

# Skill: Generate Skill Template (`generate_skill_template`)

This skill is designed to guide and automate the creation of new custom skills in the project, ensuring consistency in the file structure.

## Activation and Execution Instructions
Whenever the user requests the creation of a new skill, for example with a prompt like "create a skill to manage database" or explicitly "/generate_skill_template <skill_name>":

1. **Identify the Name**:
   - If the user specified the name of the skill, normalize it to snake_case or kebab-case (e.g., `manage_deploy`).
   - If the skill name was **not** provided, ask the user for it in a text response. Do **not** call any tools or execute any commands until you have a valid skill name from the user.
2. **Execute the Automation**:
   - First, find the absolute path of `generate_template.py`. You can use `FIND_FILE` or `SEARCH_DIR` to search for it (it resides inside the `antgravity_cli` folder under `builtin_agents/skills/generate_skill_template/scripts/`).
   - Run the script with Python using the `RUN_COMMAND` tool:
     ```powershell
     python <absolute_path_to_generate_template.py> <skill_name>
     ```
3. **Explain the Structure**: After successful creation, explain to the user what each part of the new structure does:
   - **`SKILL.md`**: Defines the name, description (YAML frontmatter) and the behavioral instructions that will be injected when the agent's skill is activated (via `/skill_name`).
   - **`scripts/`**: Folder to store executable Python or Shell scripts that the agent can call via `run_command` to perform automated actions.
   - **`examples/`**: Supporting folder with practical examples of code usage or the skill itself.
   - **`references/`**: Folder to store technical documentation, manuals, or quick reference guides to orient the agent.
