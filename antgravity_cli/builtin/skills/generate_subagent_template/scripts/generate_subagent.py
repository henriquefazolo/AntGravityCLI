#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script responsible for generating the standard directory structure and template files
for new subagents in the Google Antigravity ecosystem.
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
        description="Generates the structure and template files for a new modular subagent."
    )
    parser.add_argument(
        "name", 
        help="Name of the subagent to be created (e.g., `log_analyzer`, `git_helper`)"
    )
    parser.add_argument(
        "--output-dir", "-o", 
        default=None, 
        help="Destination directory (default: `.agents/subagents/<subagent_name>`)"
    )

    args = parser.parse_args()

    # Normalize subagent name: lowercase, replace spaces and hyphens with underscores
    subagent_name = args.name.strip().lower().replace(" ", "_").replace("-", "_")
    
    # Determine destination directory
    if args.output_dir:
        dest_dir = args.output_dir
    else:
        dest_dir = os.path.join(".agents", "subagents", subagent_name)

    print(f"=== GENERATING SUBAGENT TEMPLATE: '{subagent_name}' ===")
    print(f"Target directory: {os.path.abspath(dest_dir)}")

    if os.path.exists(dest_dir):
        print(f"WARNING: The directory '{dest_dir}' already exists. Existing files may be overwritten/updated.")

    # Create subdirectories for the Antigravity subagent pattern
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "references"), exist_ok=True)

    # 1. Generate AGENT.md (Required)
    agent_md_content = f"""---
name: "{subagent_name}"
description: "Describe concisely what this subagent is specialized in to guide the parent agent's delegation."
capabilities:
  enabled_tools:
    - VIEW_FILE
tools: []
---

# Subagent: {args.name}

Detailed system instructions and guidelines for this subagent...
"""
    create_file_with_content(os.path.join(dest_dir, "AGENT.md"), agent_md_content)

    # 2. Generate a model/supporting executable tool script (Optional)
    tool_model_content = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Example tool script for the subagent: {subagent_name}.
Any custom Python tools used by this subagent must also be added
to the main agent's tools list to be available during execution.
\"\"\"
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tool for {subagent_name}")
    parser.add_argument("--param", type=str, default="default", help="Example parameter")
    args = parser.parse_args()

    print(f"[*] Running tool for subagent: {subagent_name}")
    print(f"[*] Parameter received: {{args.param}}")
    print("[+] Success!")
    sys.exit(0)

if __name__ == "__main__":
    main()
"""
    create_file_with_content(os.path.join(dest_dir, "scripts", "example_tool.py"), tool_model_content)

    # 3. Generate reference guide file
    reference_content = f"""# Technical References: {subagent_name}

Add manuals, guidelines, or operational notes for the subagent to consult here.
"""
    create_file_with_content(os.path.join(dest_dir, "references", "README.md"), reference_content)

    print("\n[OK] Subagent structure generated successfully!")
    print(f"    Your new subagent is available at: {dest_dir}")

if __name__ == "__main__":
    main()
