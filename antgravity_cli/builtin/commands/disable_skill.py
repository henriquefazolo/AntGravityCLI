import os
import click
from colorama import Fore, Style
from .base import REPLCommand

class DisableSkillCommand(REPLCommand):
    """Command that disables a global skill in the active REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/disable_skill"]

    @property
    def description_key(self) -> str:
        return "command_disable_skill_desc"

    async def execute(self, agent, context=None) -> bool:
        if not context or not context.strip():
            click.echo(f"{Fore.RED}Error: Please specify the name of the skill to disable (e.g., /disable_skill create_txt_file){Style.RESET_ALL}")
            return True
            
        skill_name = context.strip()
        if skill_name.startswith("/"):
            skill_name = skill_name[1:]
            
        if not hasattr(agent, "_disabled_skills"):
            agent._disabled_skills = set()
            
        # Check if skill exists
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        ws_context = getattr(config, "_ws_context", None)
        if ws_context is None:
            from ...workspace_context import WorkspaceContext
            ws_context = WorkspaceContext(
                workspaces=getattr(config, "workspaces", None),
                skills_paths=getattr(config, "skills_paths", None)
            )
            
        discovered_skills = ws_context.discover_skills()
        
        if skill_name not in discovered_skills:
            click.echo(f"{Fore.YELLOW}Warning: Skill '{skill_name}' not found among active skills.{Style.RESET_ALL}")
            
        agent._disabled_skills.add(skill_name)
        click.echo(f"{Fore.GREEN}Skill '{skill_name}' has been disabled for this session.{Style.RESET_ALL}")
        return True
