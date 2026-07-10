import os
import click
from colorama import Fore, Style
from .base import REPLCommand

class HelpCommand(REPLCommand):
    """Command that lists all special REPL commands, active skills, and subagents."""

    @property
    def triggers(self) -> list[str]:
        return ["/help", "?"]

    @property
    def description_key(self) -> str:
        return "command_help_desc"

    async def execute(self, agent, context=None) -> bool:
        from ... import i18n
        
        click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== AntGravity CLI Help ==={Style.RESET_ALL}")
        
        # 1. Special commands
        click.echo(f"\n{Fore.CYAN}Special Commands:{Style.RESET_ALL}")
        from . import get_command_map
        seen = set()
        for cmd in get_command_map().values():
            if cmd in seen:
                continue
            seen.add(cmd)
            triggers_str = ", ".join([f"{Fore.GREEN}{t}{Style.RESET_ALL}" for t in cmd.triggers])
            click.echo(f"  {triggers_str:<40} - {i18n.t('repl', cmd.description_key)}")
            
        # 2. Active Skills
        click.echo(f"\n{Fore.CYAN}Active Skills:{Style.RESET_ALL}")
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        disabled_skills = getattr(agent, "_disabled_skills", set())
        
        ws_context = getattr(config, "_ws_context", None)
        if ws_context is None:
            from ...workspace_context import WorkspaceContext
            ws_context = WorkspaceContext(
                workspaces=getattr(config, "workspaces", None),
                skills_paths=getattr(config, "skills_paths", None)
            )
            
        discovered_skills = ws_context.discover_skills()
        
        if discovered_skills:
            for s in discovered_skills:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if s in disabled_skills else ""
                click.echo(f"  {Fore.GREEN}/{s:<25}{Style.RESET_ALL}{status} - {i18n.t('list_skills', s + '_desc', default='Active skill trigger')}")
        else:
            click.echo("  No active skills found.")

        # 3. Colony Subagents
        click.echo(f"\n{Fore.CYAN}Colony Subagents (Ants):{Style.RESET_ALL}")
        disabled_agents = getattr(agent, "_disabled_subagents", set())
        
        all_subagents = ws_context.discover_subagents()
        if all_subagents:
            for sa in all_subagents:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if sa.name in disabled_agents else ""
                click.echo(f"  {Fore.GREEN}:{sa.name:<25}{Style.RESET_ALL}{status} - {sa.description}")
        else:
            click.echo("  No subagents registered in the colony.")
            
        click.echo(f"\n{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")
        return True
