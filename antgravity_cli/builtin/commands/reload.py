import os
import click
from colorama import Fore, Style
from .base import REPLCommand
from ... import i18n

class ReloadCommand(REPLCommand):
    """Command that invalidates caches and reloads subagents and skills in the active session."""

    @property
    def triggers(self) -> list[str]:
        return ["/reload"]

    @property
    def description_key(self) -> str:
        return "command_reload_desc"

    async def execute(self, agent, context=None) -> bool:
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        ws_context = getattr(config, "_ws_context", None)
        if ws_context is None:
            from ...workspace_context import WorkspaceContext
            workspaces = getattr(config, "workspaces", []) or [os.path.abspath(".")]
            ws_context = WorkspaceContext(workspaces=workspaces, skills_paths=getattr(config, "skills_paths", None))
            if config:
                config._ws_context = ws_context
        
        ws_context.invalidate_cache()
        # Force refresh discovery
        discovered_subagents = ws_context.discover_subagents(force_refresh=True)
        discovered_skills = ws_context.discover_skills(force_refresh=True)
        
        # Sync subagents to config
        disabled_agents = getattr(agent, "_disabled_subagents", set())
        active_subagents = [sa for sa in discovered_subagents if sa.name not in disabled_agents and sa.name != "subagent_example"]
        if config:
            config.subagents = active_subagents
            
        click.echo(f"{Fore.GREEN}{i18n.t('commands', 'reload_success_message', skills_count=len(discovered_skills), agents_count=len(active_subagents))}{Style.RESET_ALL}")
        return True
