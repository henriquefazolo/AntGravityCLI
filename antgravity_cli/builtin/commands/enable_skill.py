import click
from colorama import Fore, Style
from .base import REPLCommand

class EnableSkillCommand(REPLCommand):
    """Command that enables a previously disabled global skill in the active REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/enable_skill"]

    @property
    def description_key(self) -> str:
        return "command_enable_skill_desc"

    async def execute(self, agent, context=None) -> bool:
        from ... import i18n
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'error_specify_skill_enable')}{Style.RESET_ALL}")
            return True
            
        skill_name = context.strip()
        if skill_name.startswith("/"):
            skill_name = skill_name[1:]
            
        if hasattr(agent, "_disabled_skills") and skill_name in agent._disabled_skills:
            agent._disabled_skills.remove(skill_name)
            click.echo(f"{Fore.GREEN}{i18n.t('commands', 'skill_enabled_success', skill_name=skill_name)}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'skill_not_disabled', skill_name=skill_name)}{Style.RESET_ALL}")
        return True
