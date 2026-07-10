import click
from colorama import Fore, Style
from .base import REPLCommand

class AntsCommand(REPLCommand):
    """Command that lists details of all registered subagents (ants)."""

    @property
    def triggers(self) -> list[str]:
        return ["/ants", "/subagents"]

    @property
    def description_key(self) -> str:
        return "command_ants_desc"

    async def execute(self, agent, context=None) -> bool:
        import os
        click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== Colony Subagents (Ants) ==={Style.RESET_ALL}")
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        disabled_agents = getattr(agent, "_disabled_subagents", set())
        
        # Discover all subagents
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
                status = f" [{Fore.RED}DISABLED{Fore.RESET}]" if sa.name in disabled_agents else f" [{Fore.GREEN}ACTIVE{Fore.RESET}]"
                click.echo(f"  {Fore.GREEN}:{sa.name:<25}{Style.RESET_ALL}{status} - {sa.description}")
                if sa.capabilities:
                    enabled = [t.value for t in getattr(sa.capabilities, "enabled_tools", []) or []]
                    disabled = [t.value for t in getattr(sa.capabilities, "disabled_tools", []) or []]
                    if enabled:
                        click.echo(f"    Tools allowed: {', '.join(enabled)}")
                    if disabled:
                        click.echo(f"    Tools denied: {', '.join(disabled)}")
                if sa.tools:
                    tool_names = []
                    for t in sa.tools:
                        if isinstance(t, str):
                            tool_names.append(t)
                        elif hasattr(t, "__name__"):
                            tool_names.append(t.__name__)
                    if tool_names:
                        click.echo(f"    Custom tools: {', '.join(tool_names)}")
        else:
            click.echo("  No subagents registered in this colony.")
            
        click.echo(f"\n{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")
        return True
