import os
import click
from colorama import Fore, Style
from .base import REPLCommand

def get_skill_description(skill_name: str, ws_context) -> str:
    """Finds a skill's SKILL.md, parses its frontmatter, and returns its description."""
    import os
    from ...utils import parse_yaml_frontmatter
    for base_path in ws_context.get_skills_search_paths():
        skill_dir = os.path.join(base_path, skill_name)
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if os.path.isfile(skill_md_path):
            try:
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                meta, _ = parse_yaml_frontmatter(content)
                if meta and "description" in meta:
                    return str(meta["description"])
            except Exception:
                pass
    return ""

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
        
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        disabled_skills = getattr(agent, "_disabled_skills", set())
        
        ws_context = getattr(config, "_ws_context", None)
        if ws_context is None:
            from ...workspace_context import WorkspaceContext
            ws_context = WorkspaceContext(
                workspaces=getattr(config, "workspaces", None),
                skills_paths=getattr(config, "skills_paths", None)
            )
            if config:
                config._ws_context = ws_context
        
        click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== AntGravity CLI Help ==={Style.RESET_ALL}")
        
        # 1. Special commands
        click.echo(f"\n{Fore.CYAN}Special Commands:{Style.RESET_ALL}")
        from . import get_command_map
        seen = set()
        for cmd in get_command_map(ws_context.workspaces).values():
            if cmd in seen:
                continue
            seen.add(cmd)
            triggers_str = ", ".join([f"{Fore.GREEN}{t}{Style.RESET_ALL}" for t in cmd.triggers])
            click.echo(f"  {triggers_str:<40} - {i18n.t('repl', cmd.description_key)}")
            
        # 2. Active Skills
        click.echo(f"\n{Fore.CYAN}Active Skills:{Style.RESET_ALL}")
        discovered_skills = ws_context.discover_skills()
        
        if discovered_skills:
            for s in discovered_skills:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if s in disabled_skills else ""
                desc = get_skill_description(s, ws_context)
                if not desc:
                    desc_key = f"{s}_desc"
                    translated = i18n.t('list_skills', desc_key)
                    if translated != desc_key:
                        desc = translated
                    else:
                        desc = i18n.t('list_skills', 'default_skill_desc')
                click.echo(f"  {Fore.GREEN}/{s:<25}{Style.RESET_ALL}{status} - {desc}")
        else:
            click.echo(i18n.t("commands", "no_active_skills"))

        # 3. Colony Subagents
        click.echo(f"\n{Fore.CYAN}Colony Subagents (Ants):{Style.RESET_ALL}")
        disabled_agents = getattr(agent, "_disabled_subagents", set())
        
        all_subagents = ws_context.discover_subagents()
        if all_subagents:
            for sa in all_subagents:
                status = f" [{Fore.RED}disabled{Fore.CYAN}]" if sa.name in disabled_agents else ""
                click.echo(f"  {Fore.GREEN}:{sa.name:<25}{Style.RESET_ALL}{status} - {sa.description}")
        else:
            click.echo(i18n.t("commands", "no_subagents_registered"))
            
        # 4. Autocomplete Shortcuts
        click.echo(f"\n{Fore.CYAN}{i18n.t('repl', 'autocomplete_shortcuts_label')}{Style.RESET_ALL}")
        click.echo(f"  {Fore.GREEN}{'/':<25}{Style.RESET_ALL} - {i18n.t('repl', 'shortcut_commands_skills')}")
        click.echo(f"  {Fore.GREEN}{'@':<25}{Style.RESET_ALL} - {i18n.t('repl', 'shortcut_files')}")
        click.echo(f"  {Fore.GREEN}{':':<25}{Style.RESET_ALL} - {i18n.t('repl', 'shortcut_subagents')}")
            
        click.echo(f"\n{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")
        return True
