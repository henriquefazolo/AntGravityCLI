import colorama
from colorama import Fore, Style
from ..interfaces import InputReader
from .. import i18n
from .completer import AntCompleter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.history import FileHistory
    HAS_PROMPT_TOOLKIT = True
else:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.history import FileHistory
        HAS_PROMPT_TOOLKIT = True
    except ImportError:
        HAS_PROMPT_TOOLKIT = False

# colorama is initialized globally in main.py

class ConsoleInputReader(InputReader):
    """Concrete terminal input reader using input() or prompt_toolkit (SRP)."""
    def __init__(self):
        self._session = None

    async def read_input(self, prompt_text: str, suggestions: list[str] | None = None, file_suggestions: list[str] | None = None, subagent_suggestions: list[str] | None = None) -> str:
        prompt_with_color = f"\n{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        
        if HAS_PROMPT_TOOLKIT:
            try:
                # Initialize the session on-demand with custom multiline support
                if self._session is None:
                    from ..utils import get_history_file_path
                    history_file = get_history_file_path()
                    
                    from prompt_toolkit.key_binding import KeyBindings
                    from prompt_toolkit.filters import completion_is_selected
                    
                    kb = KeyBindings()
                    
                    @kb.add('enter', filter=~completion_is_selected)
                    @kb.add('c-m', filter=~completion_is_selected)
                    def _(event):
                        event.current_buffer.validate_and_handle()
                        
                    @kb.add('c-j')
                    def _(event):
                        event.current_buffer.newline()
                        
                    self._session = PromptSession(
                        history=FileHistory(history_file),
                        key_bindings=kb,
                        multiline=True
                    )
                
                if suggestions or file_suggestions or subagent_suggestions:
                    completer = AntCompleter(
                        command_suggestions=suggestions or [],
                        file_suggestions=file_suggestions or [],
                        subagent_suggestions=subagent_suggestions or []
                    )
                else:
                    completer = None
                
                # Use prompt_toolkit's async session with multiline native support
                line = await self._session.prompt_async(
                    ANSI(prompt_with_color),
                    completer=completer,
                    complete_while_typing=True
                )
                return line.strip()
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # Fallback to standard input if prompt_toolkit initialization fails
                pass

        # Fallback multi-line reading with standard input() or when prompt_toolkit is unavailable
        lines = []
        current_prompt = prompt_with_color
        while True:
            try:
                line = input(current_prompt)
            except (KeyboardInterrupt, EOFError):
                raise
                
            if line.endswith('\\'):
                lines.append(line[:-1].rstrip())
                current_prompt = f"{Fore.CYAN}> {Style.RESET_ALL}"
            else:
                lines.append(line)
                break
                
        return "\n".join(lines).strip()
