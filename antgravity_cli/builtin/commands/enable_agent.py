import click
from colorama import Fore, Style
from .base import REPLCommand

class EnableAgentCommand(REPLCommand):
    """Command that enables a previously disabled colony subagent in the active REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/enable_agent"]

    @property
    def description_key(self) -> str:
        return "command_enable_agent_desc"

    async def execute(self, agent, context=None) -> bool:
        if not context or not context.strip():
            click.echo(f"{Fore.RED}Error: Please specify the name of the subagent to enable (e.g., /enable_agent log_analyzer){Style.RESET_ALL}")
            return True
            
        agent_name = context.strip()
        if agent_name.startswith(":"):
            agent_name = agent_name[1:]
            
        target_name = None
        if hasattr(agent, "_disabled_subagents"):
            for name in list(agent._disabled_subagents):
                if name.lower() == agent_name.lower():
                    target_name = name
                    break
                    
        if target_name:
            agent._disabled_subagents.remove(target_name)
            click.echo(f"{Fore.GREEN}Subagent '{target_name}' has been enabled (delegation allowed).{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}Subagent '{agent_name}' is not currently disabled.{Style.RESET_ALL}")
        return True
