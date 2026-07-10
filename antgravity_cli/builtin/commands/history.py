import os
import click
from colorama import Fore, Style
from .base import REPLCommand
from ...utils import get_history_file_path

class HistoryCommand(REPLCommand):
    """Command that prints the last n entries of prompt history."""

    @property
    def triggers(self) -> list[str]:
        return ["/history"]

    @property
    def description_key(self) -> str:
        return "command_history_desc"

    async def execute(self, agent, context=None) -> bool:
        history_file = get_history_file_path()
        if not os.path.isfile(history_file):
            click.echo(f"{Fore.YELLOW}No history file found.{Style.RESET_ALL}")
            return True

        n = 10
        if context and context.strip():
            try:
                n = int(context.strip())
            except ValueError:
                pass

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            history_items = []
            for line in lines:
                cleaned = line.strip()
                if cleaned.startswith("+"):
                    history_items.append(cleaned[1:])
                elif cleaned:
                    history_items.append(cleaned)
            
            to_print = history_items[-n:]
            if not to_print:
                click.echo(f"{Fore.YELLOW}History is empty.{Style.RESET_ALL}")
                return True

            click.echo(f"\n{Fore.MAGENTA}=== Prompt History (last {len(to_print)}) ==={Style.RESET_ALL}")
            start_idx = max(1, len(history_items) - n + 1)
            for idx, item in enumerate(to_print, start=start_idx):
                click.echo(f"  {Fore.CYAN}{idx:<4}{Style.RESET_ALL} {item}")
        except Exception as e:
            click.echo(f"{Fore.RED}Error reading history: {e}{Style.RESET_ALL}", err=True)
            
        return True
