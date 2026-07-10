import os
import re
import logging
from typing import List, Dict, Any
from google.antigravity.types import SubagentConfig, SubagentCapabilities, BuiltinTools

import yaml

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
    
    try:
        parsed_yaml = yaml.safe_load(yaml_block) or {}
    except Exception as e:
        logging.error(f"Error parsing YAML frontmatter: {e}")
        parsed_yaml = {}

    if isinstance(parsed_yaml, dict):
        config["name"] = str(parsed_yaml.get("name", "")).strip()
        config["description"] = str(parsed_yaml.get("description", "")).strip()
        
        sys_inst_val = parsed_yaml.get("system_instructions")
        if sys_inst_val:
            config["system_instructions"] = str(sys_inst_val).strip() + "\n\n" + body
            
        config["tools"] = parsed_yaml.get("tools", [])
        if not isinstance(config["tools"], list):
            config["tools"] = [config["tools"]] if config["tools"] else []
        config["tools"] = [str(t) for t in config["tools"]]
        
        capabilities_yaml = parsed_yaml.get("capabilities")
        if isinstance(capabilities_yaml, dict):
            enabled_tools = capabilities_yaml.get("enabled_tools")
            disabled_tools = capabilities_yaml.get("disabled_tools")
            
            def map_builtin_tools(tool_names) -> list[BuiltinTools]:
                if not tool_names:
                    return []
                if not isinstance(tool_names, list):
                    tool_names = [tool_names]
                res = []
                for name in tool_names:
                    name_str = str(name).strip()
                    for member in BuiltinTools:
                        if member.value.lower() == name_str.lower() or member.name.lower() == name_str.lower():
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
