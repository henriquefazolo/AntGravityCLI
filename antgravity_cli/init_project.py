import os
import click
from colorama import Fore, Style
from . import i18n


def run_init():
    """Interactively initializes a new AntGravity project workspace."""
    click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}{i18n.t('init_project', 'title')}{Style.RESET_ALL}")
    click.echo(i18n.t('init_project', 'wizard_help'))
    
    # 1. Gather configuration interactively
    api_key = click.prompt(i18n.t('init_project', 'prompt_api_key'), default="", show_default=False)
    if api_key.strip() and not api_key.strip().startswith("AIzaSy"):
        click.echo(f"{Fore.YELLOW}{i18n.t('init_project', 'api_key_warning')}{Style.RESET_ALL}")
    model = click.prompt(i18n.t('init_project', 'prompt_model'), default="gemini-3.1-flash-lite")
    language = click.prompt(i18n.t('init_project', 'prompt_language'), default="en-us")
    yolo = click.confirm(i18n.t('init_project', 'prompt_yolo'), default=False)
    
    # 2. Create directory structure
    click.echo(f"{Fore.CYAN}{i18n.t('init_project', 'creating_structure')}{Style.RESET_ALL}")
    os.makedirs(".agents", exist_ok=True)
    os.makedirs(os.path.join(".agents", "skills"), exist_ok=True)
    os.makedirs(os.path.join(".agents", "subagents"), exist_ok=True)
    click.echo(i18n.t('init_project', 'created_folder', folder='.agents/'))
    click.echo(i18n.t('init_project', 'created_folder', folder='.agents/skills/'))
    click.echo(i18n.t('init_project', 'created_folder', folder='.agents/subagents/'))
    
    # 3. Create AGENTS.md template
    agents_md_path = os.path.join(".agents", "AGENTS.md")
    if not os.path.exists(agents_md_path):
        agents_md_content = """# Project Guidelines and Rules

This file defines global behavior rules, coding style, and technical constraints for the agents in this workspace.

## 📌 Project Standards
- Language: English (code, commits, docs)
- Preferred Stack: Python 3.11+, Click, prompt_toolkit
"""
        with open(agents_md_path, "w", encoding="utf-8") as f:
            f.write(agents_md_content)
        click.echo(i18n.t('init_project', 'created_template', filepath=agents_md_path))
    else:
        click.echo(i18n.t('init_project', 'file_exists_skipping', filepath=agents_md_path))

    # 3b. Create example skill template
    skill_example_dir = os.path.join(".agents", "skills", "skill_example")
    os.makedirs(skill_example_dir, exist_ok=True)
    skill_md_path = os.path.join(skill_example_dir, "SKILL.md")
    if not os.path.exists(skill_md_path):
        skill_md_content = """---
name: "skill_example"
description: "Example skill instructions that teach the agent how to perform a custom action."
---
# Skill Example

Describe the logical behavior and steps the agent should follow when this skill is invoked:
- Step 1: Perform action A.
- Step 2: Formulate response B.
"""
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(skill_md_content)
        click.echo(i18n.t('init_project', 'created_template', filepath=skill_md_path))

    # 3c. Create example subagent template
    subagent_example_dir = os.path.join(".agents", "subagents", "subagent_example")
    os.makedirs(subagent_example_dir, exist_ok=True)
    subagent_md_path = os.path.join(subagent_example_dir, "AGENT.md")
    if not os.path.exists(subagent_md_path):
        subagent_md_content = """---
name: "subagent_example"
description: "Example subagent showing configuration of custom capabilities and tools"
capabilities:
  enabled_tools:
    - READ_FILE
    - WRITE_FILE
---
# Subagent Example Instructions

You are subagent_example, a specialist agent designed to handle custom subtasks.
Your goal is to:
1. Receive instructions from the parent agent.
2. Run analysis and perform required tasks.
3. Return the result back to the parent agent.
"""
        with open(subagent_md_path, "w", encoding="utf-8") as f:
            f.write(subagent_md_content)
        click.echo(i18n.t('init_project', 'created_template', filepath=subagent_md_path))

    # 4. Generate/Update .env file
    env_content = f"""# ==============================================================================
# AntGravity CLI - Configurations Template (.env)
# ==============================================================================

# [Required] Gemini API Key used to connect to Google GenAI service.
# Get your API key from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY={api_key}

# [Optional] Gemini Model to be used for general tasks and conversations.
# Options: gemini-3.1-flash-lite, gemini-3.1-flash, gemini-3.1-pro
GEMINI_MODEL={model}

# [Optional] Output and UI language for console interactions and help displays.
# Options: en-us (English), pt-br (Português Brasileiro)
ANTGRAVITY_LANG={language}

# [Optional] YOLO (Safe-bypass) Mode.
# Set to 'true' to bypass safety confirmations for write/command tools.
ANTGRAVITY_YOLO={str(yolo).lower()}

# [Optional] Restricts file access tools to specified paths (space-separated).
# Example: ANTGRAVITY_WORKSPACE=C:\\workspace1 C:\\workspace2
# ANTGRAVITY_WORKSPACE=

# [Optional] Custom system instructions prompt or path to a file containing instructions.
# ANTGRAVITY_SYSTEM_INSTRUCTION=

# [Optional] Path to custom skills folders (space-separated).
# ANTGRAVITY_SKILLS_PATH=

# [Optional] Hide reasoning thoughts and tools logs in console (true / false).
# ANTGRAVITY_SILENT=false

# [Optional] Show detailed reasoning thoughts inside the console (true / false).
# ANTGRAVITY_VERBOSE=false
"""
        
    env_path = ".env"
    if os.path.exists(env_path):
        if click.confirm(i18n.t('init_project', 'file_exists_overwrite_confirm', filepath=env_path), default=False):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content.strip() + "\n")
            click.echo(i18n.t('init_project', 'overwrote_file', filepath=env_path))
        else:
            click.echo(i18n.t('init_project', 'skipped_updating', filepath=env_path))
    else:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content.strip() + "\n")
        click.echo(i18n.t('init_project', 'created_file', filepath=env_path))
        
    click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}{i18n.t('init_project', 'success_message')}{Style.RESET_ALL}")
