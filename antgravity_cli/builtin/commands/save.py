import os
import json
import click
from colorama import Fore, Style
from .base import REPLCommand
from ...utils import get_history_file_path
from ... import i18n

class SaveCommand(REPLCommand):
    """Command that saves active conversation history to a file."""

    @property
    def triggers(self) -> list[str]:
        return ["/save"]

    @property
    def description_key(self) -> str:
        return "command_save_desc"

    async def execute(self, agent, context=None) -> bool:
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'save_error_no_name')}{Style.RESET_ALL}")
            return True
            
        session_name = context.strip()
        history_dir = os.path.dirname(get_history_file_path())
        sessions_dir = os.path.join(history_dir, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        
        session_path = os.path.join(sessions_dir, f"{session_name}.json")
        try:
            history = agent.conversation.history
            serialized_history = [step.model_dump(mode='json') for step in history]
            
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(serialized_history, f, indent=2, ensure_ascii=False)
                
            click.echo(f"{Fore.GREEN}{i18n.t('commands', 'save_success', name=session_name)}{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}Error saving session: {e}{Style.RESET_ALL}", err=True)
            
        return True
