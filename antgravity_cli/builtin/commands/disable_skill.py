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
        from ... import i18n
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'error_specify_skill_disable')}{Style.RESET_ALL}")
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
            click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'warning_skill_not_found', skill_name=skill_name)}{Style.RESET_ALL}")
            
        agent._disabled_skills.add(skill_name)
        click.echo(f"{Fore.GREEN}{i18n.t('commands', 'skill_disabled_success', skill_name=skill_name)}{Style.RESET_ALL}")
        return True
