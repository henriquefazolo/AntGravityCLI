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
        from ... import i18n
        
        history_file = get_history_file_path()
        if not os.path.isfile(history_file):
            click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'history_no_file')}{Style.RESET_ALL}")
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
            
            if not history_items:
                click.echo(f"{Fore.YELLOW}{i18n.t('commands', 'history_empty')}{Style.RESET_ALL}")
                return True

            to_print = history_items[-n:]
            click.echo(f"\n{Fore.MAGENTA}{i18n.t('commands', 'history_title')}{Style.RESET_ALL}")
            
            history_start_idx = getattr(agent, "_history_start_idx", 0)
            
            printed_prev = False
            printed_active = False
            
            start_idx = max(0, len(history_items) - n)
            for idx in range(start_idx, len(history_items)):
                item = history_items[idx]
                is_active = (idx >= history_start_idx)
                
                if is_active and not printed_active:
                    if printed_prev:
                        click.echo(f"  {Fore.LIGHTBLACK_EX}----------------------{Style.RESET_ALL}")
                    click.echo(f"  {Fore.GREEN}{i18n.t('commands', 'history_active_session')}{Style.RESET_ALL}")
                    printed_active = True
                elif not is_active and not printed_prev:
                    click.echo(f"  {Fore.YELLOW}{i18n.t('commands', 'history_prev_sessions')}{Style.RESET_ALL}")
                    printed_prev = True
                    
                formatted_item = item.replace("\n", f"\n       ")
                click.echo(f"    {Fore.LIGHTBLACK_EX}{idx + 1:<4}{Style.RESET_ALL} {Fore.WHITE}{formatted_item}{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}{i18n.t('commands', 'history_error', error=str(e))}{Style.RESET_ALL}", err=True)
            
        return True
