import colorama
from colorama import Fore, Style
from ..interfaces import InputReader
from .. import i18n
from .completer import AntCompleter

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

    async def read_input(self, prompt_text: str, suggestions: list[str] = None, file_suggestions: list[str] = None, subagent_suggestions: list[str] = None) -> str:
        prompt_with_color = f"\n{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        
        lines = []
        current_prompt = prompt_with_color
        
        while True:
            if HAS_PROMPT_TOOLKIT and (suggestions or file_suggestions or subagent_suggestions):
                try:
                    # Initialize the session on-demand to avoid failure during instantiation in tests or CI/CD
                    if self._session is None:
                        from ..utils import get_history_file_path
                        history_file = get_history_file_path()
                        self._session = PromptSession(history=FileHistory(history_file))
                    
                    completer = AntCompleter(
                        command_suggestions=suggestions or [],
                        file_suggestions=file_suggestions or [],
                        subagent_suggestions=subagent_suggestions or []
                    )
                    # Use prompt_toolkit's async session integrated with asyncio
                    line = await self._session.prompt_async(
                        ANSI(current_prompt),
                        completer=completer,
                        complete_while_typing=True
                    )
                except (KeyboardInterrupt, EOFError):
                    raise
                except Exception:
                    # Safe fallback to native input() in case of prompt_toolkit errors
                    line = input(current_prompt)
            else:
                line = input(current_prompt)
                
            if line.endswith('\\'):
                lines.append(line[:-1].rstrip())
                current_prompt = f"{Fore.CYAN}> {Style.RESET_ALL}"
            else:
                lines.append(line)
                break
                
        return "\n".join(lines).strip()
