#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script responsible for generating the standard directory structure and template files
for new skills in the Google Antigravity ecosystem.
"""

import os
import sys
import argparse

def create_file_with_content(filepath: str, content: str):
    """Helper to create a file ensuring the parent directory exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  [+] Created: {filepath}")

def main():
    parser = argparse.ArgumentParser(
        description="Generates the structure and template files for a new skill."
    )
    parser.add_argument(
        "name", 
        help="Name of the skill to be created (e.g., `manage_db`, `analyze_logs`)"
    )
    parser.add_argument(
        "--output-dir", "-o", 
        default=None, 
        help="Destination directory (default: `.agents/skills/<skill_name>`)"
    )

    args = parser.parse_args()

    # Normalize skill name: lowercase, replace spaces and hyphens with underscores
    skill_name = args.name.strip().lower().replace(" ", "_").replace("-", "_")
    
    # Determine destination directory
    if args.output_dir:
        dest_dir = args.output_dir
    else:
        dest_dir = os.path.join(".agents", "skills", skill_name)

    print(f"=== GENERATING SKILL TEMPLATE: '{skill_name}' ===")
    print(f"Target directory: {os.path.abspath(dest_dir)}")

    if os.path.exists(dest_dir):
        print(f"WARNING: The directory '{dest_dir}' already exists. Existing files may be overwritten/updated.")

    # Create main subdirectories for the Antigravity pattern
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "examples"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "references"), exist_ok=True)

    # 1. Generate SKILL.md (Required)
    skill_md_content = f"""---
name: "{skill_name}"
description: "Describe concisely and clearly the main objective of this skill. This text guides the agent to load the skill when appropriate."
---

# Skill: {args.name}

This skill provides additional instructions, design rules, and automated tools for the agent to handle tasks related to: **{args.name}**.

## Guidelines and Usage Instructions
Whenever the user requests actions covered by this skill:
1. Follow the established engineering standards of the project.
2. Use the supporting scripts in the `scripts/` folder using the `run_command` tool when automation is needed.
3. Consult the documentation and examples in the `references/` and `examples/` folders if there are questions.

## Expected Behavior
- Step 1: Analyze the parameters provided by the user.
- Step 2: If necessary, execute the automation scripts in `scripts/` to assist with the tasks.
- Step 3: Provide a clear, educational explanation of the output in compliance with the project rules.
"""
    create_file_with_content(os.path.join(dest_dir, "SKILL.md"), skill_md_content)

    # 2. Generate a model/supporting executable script (Optional, but highly recommended)
    script_model_content = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Example automation script for the skill: {skill_name}.
All complex actions (validations, builds, deploys, loads) should be packaged
into scripts like this so that the agent can execute them reliably and reproducibly.
\"\"\"
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Utility script for the skill {skill_name}")
    parser.add_argument("--param", type=str, default="default_value", help="Example tool parameter")
    args = parser.parse_args()

    print(f"[*] Running automation for skill: {skill_name}")
    print(f"[*] Parameter received: {{args.param}}")
    print("[+] Success: Automation executed successfully!")
    
    # Return success code
    sys.exit(0)

if __name__ == "__main__":
    main()
"""
    create_file_with_content(os.path.join(dest_dir, "scripts", "example_automation.py"), script_model_content)

    # 3. Generate example usage file
    example_content = f"""# Usage Examples: {skill_name}

This file illustrates practical test cases and recommended usage examples for the skill **{skill_name}**.

## Example 1: Running in the terminal
You can direct the agent to run the support script if there is a corresponding task:
```powershell
python .agents/skills/{skill_name}/scripts/example_automation.py --param "my_test"
```

## Example 2: Direct prompt calls in the REPL
- "Run routine for /{skill_name}"
- "Activate /{skill_name} and detail parameters"
"""
    create_file_with_content(os.path.join(dest_dir, "examples", "usage_examples.md"), example_content)

    # 4. Generate quick reference file
    reference_content = f"""# Technical References: {skill_name}

Add API documentation, technical specifications, data schemas, external links,
or operational manuals here for the agent and developers to consult.

## Quick Guide
- Official Manual: [Insert URL or local file path]
- Critical Business Rule:
  1. Always validate format before proceeding.
  2. Never overwrite production data without a prior backup.
"""
    reference_content_path = os.path.join(dest_dir, "references", "quick_reference.md")
    create_file_with_content(reference_content_path, reference_content)

    print("\n[OK] Skill structure generated successfully!")
    print(f"    Your new skill is available at: {dest_dir}")
    print("    To activate it in the agent REPL, use the corresponding directive in the prompt (e.g., /" + skill_name + ")")

if __name__ == "__main__":
    main()
