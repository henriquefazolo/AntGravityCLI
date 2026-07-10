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
        if not context or not context.strip():
            click.echo(f"{Fore.RED}Error: Please specify the name of the skill to enable (e.g., /enable_skill create_txt_file){Style.RESET_ALL}")
            return True
            
        skill_name = context.strip()
        if hasattr(agent, "_disabled_skills") and skill_name in agent._disabled_skills:
            agent._disabled_skills.remove(skill_name)
            click.echo(f"{Fore.GREEN}Skill '{skill_name}' has been enabled for this session.{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}Skill '{skill_name}' is not currently disabled.{Style.RESET_ALL}")
        return True
