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
        if not context or not context.strip():
            click.echo(f"{Fore.RED}Error: Please specify the name of the subagent to disable (e.g., /disable_agent log_analyzer){Style.RESET_ALL}")
            return True
            
        agent_name = context.strip()
        if not hasattr(agent, "_disabled_subagents"):
            agent._disabled_subagents = set()
            
        # Check if subagent exists in discovered subagents
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        workspaces = getattr(config, "workspaces", []) or [os.path.abspath(".")]
        subagent_paths = []
        for ws in workspaces:
            workspace_subagents = os.path.join(ws, ".agents", "subagents")
            if os.path.isdir(workspace_subagents):
                subagent_paths.append(workspace_subagents)
                
        from ...subagents import discover_subagents_in_paths
        discovered_subagents = discover_subagents_in_paths(subagent_paths)
        discovered_names = [sa.name for sa in discovered_subagents]
        
        # Check case-insensitively or exact
        target_name = None
        for name in discovered_names:
            if name.lower() == agent_name.lower():
                target_name = name
                break
                
        if not target_name:
            click.echo(f"{Fore.YELLOW}Warning: Subagent '{agent_name}' not found in the colony.{Style.RESET_ALL}")
            target_name = agent_name
            
        agent._disabled_subagents.add(target_name)
        click.echo(f"{Fore.GREEN}Subagent '{target_name}' has been disabled (delegation blocked).{Style.RESET_ALL}")
        return True
