import os
import click
from colorama import Fore, Style
from .base import REPLCommand
from ... import i18n

class ConfigCommand(REPLCommand):
    """Command that prints a formatted summary of the active configurations."""

    @property
    def triggers(self) -> list[str]:
        return ["/config"]

    @property
    def description_key(self) -> str:
        return "command_config_desc"

    async def execute(self, agent, context=None) -> bool:
        config = getattr(agent, "config", None) or getattr(agent, "_config", None)
        if not config:
            click.echo(f"{Fore.RED}No active config found.{Style.RESET_ALL}")
            return True
            
        model = getattr(config, "model", "N/A")
        workspaces = getattr(config, "workspaces", [])
        skills_paths = getattr(config, "skills_paths", [])
        api_key = getattr(config, "api_key", "")
        
        masked_key = "N/A"
        if api_key:
            if len(api_key) > 10:
                masked_key = f"{api_key[:6]}...{api_key[-4:]}"
            else:
                masked_key = "********"
                
        yolo_mode = os.environ.get("ANTGRAVITY_YOLO", "false").lower() == "true"
        lang = i18n.get_language()
        
        click.echo(f"\n{Fore.MAGENTA}=== Active Configuration ==={Style.RESET_ALL}")
        click.echo(f"  {Fore.CYAN}Model:{Style.RESET_ALL}        {model}")
        click.echo(f"  {Fore.CYAN}API Key:{Style.RESET_ALL}      {masked_key}")
        click.echo(f"  {Fore.CYAN}Language:{Style.RESET_ALL}     {lang}")
        click.echo(f"  {Fore.CYAN}YOLO Mode:{Style.RESET_ALL}    {str(yolo_mode).upper()}")
        
        click.echo(f"  {Fore.CYAN}Workspaces:{Style.RESET_ALL}")
        if workspaces:
            for ws in workspaces:
                click.echo(f"    - {ws}")
        else:
            click.echo("    - (None)")
            
        click.echo(f"  {Fore.CYAN}Skills Paths:{Style.RESET_ALL}")
        if skills_paths:
            for sp in skills_paths:
                click.echo(f"    - {sp}")
        else:
            click.echo("    - (None)")
            
        click.echo(f"\n{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")
        return True
