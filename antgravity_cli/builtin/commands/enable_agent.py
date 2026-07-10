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
        from ... import i18n
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'error_specify_agent_enable')}{Style.RESET_ALL}")
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
            click.echo(f"{Fore.GREEN}{i18n.t('commands', 'agent_enabled_success', target_name=target_name)}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'agent_not_disabled', agent_name=agent_name)}{Style.RESET_ALL}")
        return True
