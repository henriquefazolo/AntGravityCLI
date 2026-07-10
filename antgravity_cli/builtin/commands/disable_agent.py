import os
import click
from colorama import Fore, Style
from .base import REPLCommand

class DisableAgentCommand(REPLCommand):
    """Command that disables a colony subagent (worker ant) in the active REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/disable_agent"]

    @property
    def description_key(self) -> str:
        return "command_disable_agent_desc"

    async def execute(self, agent, context=None) -> bool:
        from ... import i18n
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'error_specify_agent_disable')}{Style.RESET_ALL}")
            return True
            
        agent_name = context.strip()
        if agent_name.startswith(":"):
            agent_name = agent_name[1:]
            
        if not hasattr(agent, "_disabled_subagents"):
            agent._disabled_subagents = set()
            
        # Check if subagent exists in discovered subagents
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        ws_context = getattr(config, "_ws_context", None)
        if ws_context is None:
            from ...workspace_context import WorkspaceContext
            workspaces = getattr(config, "workspaces", []) or [os.path.abspath(".")]
            ws_context = WorkspaceContext(workspaces=workspaces, skills_paths=getattr(config, "skills_paths", None))
            
        discovered_subagents = ws_context.discover_subagents()
        discovered_names = [sa.name for sa in discovered_subagents]
        
        # Check case-insensitively or exact
        target_name = None
        for name in discovered_names:
            if name.lower() == agent_name.lower():
                target_name = name
                break
                
        if not target_name:
            click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'warning_agent_not_found', agent_name=agent_name)}{Style.RESET_ALL}")
            target_name = agent_name
            
        agent._disabled_subagents.add(target_name)
        click.echo(f"{Fore.GREEN}{i18n.t('commands', 'agent_disabled_success', target_name=target_name)}{Style.RESET_ALL}")
        return True
