import os
import re
import logging
from typing import List, Dict, Any
from google.antigravity.types import SubagentConfig, SubagentCapabilities, BuiltinTools

def parse_agent_md(content: str) -> dict:
    """Parses YAML frontmatter from AGENT.md content and returns a dictionary of configuration fields."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return {
            "name": "",
            "description": "",
            "system_instructions": content.strip(),
            "capabilities": None,
            "tools": []
        }
        
    yaml_block = match.group(1)
    body = match.group(2).strip()
    
    config = {
        "name": "",
        "description": "",
        "system_instructions": body,
        "capabilities": None,
        "tools": []
    }
    
    lines = yaml_block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
            
        if stripped.startswith("name:"):
            config["name"] = stripped.split(":", 1)[1].strip().strip('"\'')
        elif stripped.startswith("description:"):
            config["description"] = stripped.split(":", 1)[1].strip().strip('"\'')
        elif stripped.startswith("system_instructions:"):
            sys_inst_val = stripped.split(":", 1)[1].strip().strip('"\'')
            if sys_inst_val:
                config["system_instructions"] = sys_inst_val + "\n\n" + body
        elif stripped.startswith("tools:"):
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('-') or not lines[i].strip()):
                t_line = lines[i].strip()
                if t_line.startswith('-'):
                    tool_name = t_line[1:].strip().strip('"\'')
                    if tool_name:
                        config["tools"].append(tool_name)
                i += 1
            continue
        elif stripped.startswith("capabilities:"):
            enabled_tools = None
            disabled_tools = None
            i += 1
            while i < len(lines) and (lines[i].startswith(' ') or not lines[i].strip()):
                cap_line = lines[i].strip()
                if cap_line.startswith("enabled_tools:"):
                    enabled_tools = []
                    i += 1
                    while i < len(lines) and (lines[i].strip().startswith('-') or not lines[i].strip()):
                        item_line = lines[i].strip()
                        if item_line.startswith('-'):
                            tool_name = item_line[1:].strip().strip('"\'')
                            if tool_name:
                                enabled_tools.append(tool_name)
                        i += 1
                    continue
                elif cap_line.startswith("disabled_tools:"):
                    disabled_tools = []
                    i += 1
                    while i < len(lines) and (lines[i].strip().startswith('-') or not lines[i].strip()):
                        item_line = lines[i].strip()
                        if item_line.startswith('-'):
                            tool_name = item_line[1:].strip().strip('"\'')
                            if tool_name:
                                disabled_tools.append(tool_name)
                        i += 1
                    continue
                i += 1
            
            def map_builtin_tools(tool_names: list[str]) -> list[BuiltinTools]:
                res = []
                for name in tool_names:
                    for member in BuiltinTools:
                        if member.value.lower() == name.lower() or member.name.lower() == name.lower():
                            res.append(member)
                            break
                return res
            
            caps = {}
            if enabled_tools is not None:
                caps["enabled_tools"] = map_builtin_tools(enabled_tools)
            if disabled_tools is not None:
                caps["disabled_tools"] = map_builtin_tools(disabled_tools)
                
            if caps:
                config["capabilities"] = SubagentCapabilities(**caps)
            continue
            
        i += 1
        
    return config

def discover_subagents_in_paths(paths: List[str]) -> List[SubagentConfig]:
    """Scans the provided directories for modular subagent folders containing an AGENT.md file.
    
    Args:
        paths: List of directories to search.
        
    Returns:
        List[SubagentConfig]: Dynamically created configurations for discovered subagents.
    """
    subagents = []
    if not paths:
        return []
        
    for path in paths:
        if not path or not os.path.isdir(path):
            continue
            
        try:
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    agent_md_path = os.path.join(entry_path, "AGENT.md")
                    if os.path.isfile(agent_md_path):
                        try:
                            with open(agent_md_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            config = parse_agent_md(content)
                            
                            # Fallback if name is empty to use the directory name
                            name = config.get("name") or entry
                            description = config.get("description") or f"Subagent {name}"
                            
                            subagent = SubagentConfig(
                                name=name,
                                description=description,
                                system_instructions=config.get("system_instructions"),
                                capabilities=config.get("capabilities"),
                                tools=config.get("tools") or []
                            )
                            subagents.append(subagent)
                        except Exception as e:
                            logging.error(f"Error loading subagent from {agent_md_path}: {e}")
        except Exception as e:
            logging.error(f"Error listing subagent path {path}: {e}")
            
    # Sort subagents by name to keep deterministic order
    return sorted(subagents, key=lambda x: x.name)
