import os
import click
from colorama import Fore, Style
from .base import REPLCommand

class DisableSkillCommand(REPLCommand):
    """Command that disables a global skill in the active REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/disable_skill"]

    @property
    def description_key(self) -> str:
        return "command_disable_skill_desc"

    async def execute(self, agent, context=None) -> bool:
        if not context or not context.strip():
            click.echo(f"{Fore.RED}Error: Please specify the name of the skill to disable (e.g., /disable_skill create_txt_file){Style.RESET_ALL}")
            return True
            
        skill_name = context.strip()
        if not hasattr(agent, "_disabled_skills"):
            agent._disabled_skills = set()
            
        # Check if skill exists
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        skills_paths = getattr(config, "skills_paths", None) or []
        from ...list_skills import discover_skills_in_paths
        from ...utils import get_base_path
        base_dir = get_base_path()
        cli_skills_dir = os.path.join(base_dir, "builtin", "skills")
        paths_to_search = list(skills_paths) if skills_paths else ["skills", ".agents/skills", cli_skills_dir]
        discovered_skills = discover_skills_in_paths(paths_to_search)
        
        if skill_name not in discovered_skills:
            click.echo(f"{Fore.YELLOW}Warning: Skill '{skill_name}' not found among active skills.{Style.RESET_ALL}")
            
        agent._disabled_skills.add(skill_name)
        click.echo(f"{Fore.GREEN}Skill '{skill_name}' has been disabled for this session.{Style.RESET_ALL}")
        return True
