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
        skills_paths = getattr(config, "skills_paths", None) or []
        disabled_skills = getattr(agent, "_disabled_skills", set())
        
        from ...list_skills import discover_skills_in_paths
        from ...utils import get_base_path
        base_dir = get_base_path()
        cli_skills_dir = os.path.join(base_dir, "builtin", "skills")
        paths_to_search = list(skills_paths) if skills_paths else ["skills", ".agents/skills", cli_skills_dir]
        discovered_skills = discover_skills_in_paths(paths_to_search)
        
        if discovered_skills:
            for s in discovered_skills:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if s in disabled_skills else ""
                click.echo(f"  {Fore.GREEN}/{s:<25}{Style.RESET_ALL}{status} - {i18n.t('list_skills', s + '_desc', default='Active skill trigger')}")
        else:
            click.echo("  No active skills found.")

        # 3. Colony Subagents
        click.echo(f"\n{Fore.CYAN}Colony Subagents (Ants):{Style.RESET_ALL}")
        disabled_agents = getattr(agent, "_disabled_subagents", set())
        workspaces = getattr(config, "workspaces", []) or [os.path.abspath(".")]
        subagent_paths = []
        for ws in workspaces:
            workspace_subagents = os.path.join(ws, ".agents", "subagents")
            if os.path.isdir(workspace_subagents):
                subagent_paths.append(workspace_subagents)
                
        from ...subagents import discover_subagents_in_paths
        all_subagents = discover_subagents_in_paths(subagent_paths)
        if all_subagents:
            for sa in all_subagents:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if sa.name in disabled_agents else ""
                click.echo(f"  {Fore.GREEN}:{sa.name:<25}{Style.RESET_ALL}{status} - {sa.description}")
        else:
            click.echo("  No subagents registered in the colony.")
            
        click.echo(f"\n{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")
        return True
