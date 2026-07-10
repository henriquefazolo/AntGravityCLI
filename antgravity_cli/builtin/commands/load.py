import os
import json
import click
from colorama import Fore, Style
from .base import REPLCommand
from ...utils import get_history_file_path
from ... import i18n
from google.antigravity.types import Step

class LoadCommand(REPLCommand):
    """Command that loads conversation history from a file."""

    @property
    def triggers(self) -> list[str]:
        return ["/load"]

    @property
    def description_key(self) -> str:
        return "command_load_desc"

    async def execute(self, agent, context=None) -> bool:
        if not context or not context.strip():
            click.echo(f"{Fore.RED}{i18n.t('commands', 'load_error_no_name')}{Style.RESET_ALL}")
            return True
            
        session_name = context.strip()
        history_dir = os.path.dirname(get_history_file_path())
        session_path = os.path.join(history_dir, "sessions", f"{session_name}.json")
        
        if not os.path.isfile(session_path):
            click.echo(f"{Fore.RED}{i18n.t('commands', 'load_error_not_found', name=session_name)}{Style.RESET_ALL}")
            return True
            
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                serialized_history = json.load(f)
                
            steps = []
            for step_data in serialized_history:
                steps.append(Step.model_validate(step_data))
                
            agent.conversation.history = steps
            click.echo(f"{Fore.GREEN}{i18n.t('commands', 'load_success', name=session_name, count=len(steps))}{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}Error loading session: {e}{Style.RESET_ALL}", err=True)
            
        return True
