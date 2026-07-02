import os
import click
from colorama import Fore, Style
from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy

import i18n
from handlers import cli_ask_user_handler

def setup_agent_config(model, yolo, workspace, system_instruction, api_key, skills_path) -> LocalAgentConfig:
    """Configures and returns the agent's LocalAgentConfig, resolving keys, paths, and policies."""
    # 1. Resolve API Key
    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not resolved_api_key:
        raise ValueError(i18n.t("config", "api_key_not_found"))

    # 2. Configure Permission Policies
    resolved_workspace = [os.path.abspath(w) for w in workspace] if workspace else [os.path.abspath(".")]
    policies_list = []
    for p in policy.workspace_only(resolved_workspace):
        policies_list.append(p)

    if yolo:
        policies_list.append(policy.allow_all())
        click.echo(f"{Fore.LIGHTRED_EX}{i18n.t('config', 'yolo_warning')}{Style.RESET_ALL}")
    else:
        for p in policy.confirm_run_command(handler=cli_ask_user_handler):
            policies_list.append(p)

    # 3. Resolve System Instructions
    sys_inst = None
    if system_instruction:
        if os.path.isfile(system_instruction):
            try:
                with open(system_instruction, "r", encoding="utf-8") as f:
                    sys_inst = f.read()
            except Exception as e:
                raise IOError(i18n.t("config", "error_reading_instructions", error=str(e)))
        else:
            sys_inst = system_instruction

    # 4. Resolve Skills
    resolved_skills = list(skills_path) if skills_path else []
    if not resolved_skills and os.path.isdir("skills"):
        resolved_skills.append("skills")

    # 5. Build Agent Configuration
    return LocalAgentConfig(
        model=model,
        api_key=resolved_api_key,
        policies=policies_list,
        system_instructions=sys_inst,
        workspaces=resolved_workspace,
        skills_paths=resolved_skills if resolved_skills else None
    )
