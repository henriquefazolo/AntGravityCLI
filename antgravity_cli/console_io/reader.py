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

# Initialize colorama for console color support (especially Windows)
colorama.init()

class ConsoleInputReader(InputReader):
    """Concrete terminal input reader using input() or prompt_toolkit (SRP)."""
    def __init__(self):
        self._session = None

    async def read_input(self, prompt_text: str, suggestions: list[str] = None, file_suggestions: list[str] = None, subagent_suggestions: list[str] = None) -> str:
        prompt_with_color = f"\n{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        
        if HAS_PROMPT_TOOLKIT and (suggestions or file_suggestions or subagent_suggestions):
            try:
                # Initialize the session on-demand to avoid failure during instantiation in tests or CI/CD
                if self._session is None:
                    import os
                    history_file = os.path.expanduser("~/.antgravity_history")
                    self._session = PromptSession(history=FileHistory(history_file))
                
                completer = AntCompleter(
                    command_suggestions=suggestions or [],
                    file_suggestions=file_suggestions or [],
                    subagent_suggestions=subagent_suggestions or []
                )
                # Use prompt_toolkit's async session integrated with asyncio
                return (await self._session.prompt_async(
                    ANSI(prompt_with_color),
                    completer=completer,
                    complete_while_typing=True
                )).strip()
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # Safe fallback to native input() in case of prompt_toolkit errors (e.g. NoConsoleScreenBufferError)
                return input(prompt_with_color).strip()
        else:
            return input(prompt_with_color).strip()
