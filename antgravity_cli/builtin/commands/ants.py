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

    async def execute(self, agent) -> bool:
        click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== Colony Subagents (Ants) ==={Style.RESET_ALL}")
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        subagents = getattr(config, "subagents", [])
        
        if subagents:
            for sa in subagents:
                click.echo(f"  {Fore.GREEN}:{sa.name:<25}{Style.RESET_ALL} - {sa.description}")
                if sa.capabilities:
                    enabled = [t.value for t in getattr(sa.capabilities, "enabled_tools", []) or []]
                    disabled = [t.value for t in getattr(sa.capabilities, "disabled_tools", []) or []]
                    if enabled:
                        click.echo(f"    Tools allowed: {', '.join(enabled)}")
                    if disabled:
                        click.echo(f"    Tools denied: {', '.join(disabled)}")
                if sa.tools:
                    # sa.tools can contain string names or callables
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
