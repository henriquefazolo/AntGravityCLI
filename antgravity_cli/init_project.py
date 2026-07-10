import os
import click
from colorama import Fore, Style

def run_init():
    """Interactively initializes a new AntGravity project workspace."""
    click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== AntGravity Project Initializer ==={Style.RESET_ALL}")
    click.echo("This wizard will help you set up a local workspace customization folder (.agents) and a .env file.\n")
    
    # 1. Gather configuration interactively
    api_key = click.prompt("Gemini API Key (leave empty to skip)", default="", show_default=False)
    model = click.prompt("Gemini Model", default="gemini-3.1-flash-lite")
    language = click.prompt("Language (en-us, pt-br)", default="en-us")
    yolo = click.confirm("Enable YOLO Mode (bypass safety confirmations)?", default=False)
    
    # 2. Create directory structure
    click.echo(f"\n[*] Creating workspace structure...")
    os.makedirs(".agents", exist_ok=True)
    os.makedirs(os.path.join(".agents", "skills"), exist_ok=True)
    os.makedirs(os.path.join(".agents", "subagents"), exist_ok=True)
    click.echo(f"  [+] Created folder: .agents/")
    click.echo(f"  [+] Created folder: .agents/skills/")
    click.echo(f"  [+] Created folder: .agents/subagents/")
    
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
        click.echo(f"  [+] Created template: {agents_md_path}")
    else:
        click.echo(f"  [!] File '{agents_md_path}' already exists, skipping template creation.")

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
        click.echo(f"  [+] Created template: {skill_md_path}")

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
tools:
  - run_custom_analyzer
---
# Subagent Example Instructions

You are subagent_example, a specialist agent designed to handle custom subtasks.
Your goal is to:
1. Receive instructions from the parent agent.
2. Run custom analysis using your tools.
3. Return the result back to the parent agent.
"""
        with open(subagent_md_path, "w", encoding="utf-8") as f:
            f.write(subagent_md_content)
        click.echo(f"  [+] Created template: {subagent_md_path}")

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
        if click.confirm(f"A '{env_path}' file already exists. Do you want to overwrite it?", default=False):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content.strip() + "\n")
            click.echo(f"  [+] Overwrote: {env_path}")
        else:
            click.echo(f"  [!] Skipped updating {env_path}")
    else:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content.strip() + "\n")
        click.echo(f"  [+] Created: {env_path}")
        
    click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}[OK] AntGravity project initialized successfully!{Style.RESET_ALL}")
