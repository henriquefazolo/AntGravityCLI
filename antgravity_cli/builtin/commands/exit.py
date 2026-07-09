import click
from colorama import Fore, Style
from antgravity_cli import i18n
from .base import REPLCommand

class ExitCommand(REPLCommand):
    """Command that terminates the interactive REPL session."""

    @property
    def triggers(self) -> list[str]:
        return ["/exit", "/quit"]

    @property
    def description_key(self) -> str:
        return "command_exit_desc"

    async def execute(self, agent, context=None) -> bool:
        click.echo(f"{Fore.YELLOW}{i18n.t('repl', 'exiting')}{Style.RESET_ALL}")
        return False
