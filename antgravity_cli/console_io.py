import asyncio
import re
import colorama
from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from . import i18n
from .interfaces import OutputWriter, InputReader

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter, Completer, Completion
    from prompt_toolkit.formatted_text import ANSI
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

if HAS_PROMPT_TOOLKIT:
    # Pattern to match slash commands as a single word in prompt-toolkit
    _PATTERN_CMD = re.compile(r'/[a-zA-Z0-9_-]*')

    class CommandCompleter(WordCompleter):
        """Custom WordCompleter that triggers only when the word before cursor starts with a slash '/'."""
        def get_completions(self, document, complete_event):
            word_before_cursor = ""
            if self.pattern:
                matches = list(self.pattern.finditer(document.text_before_cursor))
                if matches:
                    match = matches[-1]
                    if match.end() == len(document.text_before_cursor):
                        word_before_cursor = match.group()
            
            if not word_before_cursor.startswith('/'):
                return
                
            yield from super().get_completions(document, complete_event)

    class AntCompleter(Completer):
        """Unified completer for slash commands and at-sign file/folder suggestions."""
        def __init__(self, command_suggestions: list[str], file_suggestions: list[str]):
            self.command_suggestions = command_suggestions
            self.file_suggestions = file_suggestions
            self._pattern_cmd = re.compile(r'/[a-zA-Z0-9_-]*')
            self._pattern_file = re.compile(r'@[a-zA-Z0-9_\-\./\\]*')

        def get_completions(self, document, complete_event):
            text_before = document.text_before_cursor

            # 1. Command completion (starts with /)
            cmd_matches = list(self._pattern_cmd.finditer(text_before))
            if cmd_matches and cmd_matches[-1].end() == len(text_before):
                match = cmd_matches[-1]
                word = match.group()
                for suggestion in self.command_suggestions:
                    if suggestion.lower().startswith(word.lower()):
                        yield Completion(suggestion, start_position=-len(word))
                return

            # 2. File and folder completion (starts with @)
            file_matches = list(self._pattern_file.finditer(text_before))
            if file_matches and file_matches[-1].end() == len(text_before):
                match = file_matches[-1]
                word = match.group()
                prefix = word[1:] # strip the '@'
                prefix_lower = prefix.lower()
                # Yield prefix matches first
                for suggestion in self.file_suggestions:
                    if suggestion.lower().startswith(prefix_lower):
                        yield Completion(f"@{suggestion}", start_position=-len(word))
                # Yield substring/middle matches next
                for suggestion in self.file_suggestions:
                    if prefix_lower in suggestion.lower() and not suggestion.lower().startswith(prefix_lower):
                        yield Completion(f"@{suggestion}", start_position=-len(word))

# Initialize colorama for console color support (especially Windows)
colorama.init()

class ConsoleOutputWriter(OutputWriter):
    """Concrete terminal output writer using colorama and rich for Markdown (SRP)."""
    def __init__(self):
        self._first_text = True
        self._console = Console(force_terminal=True)
        self._text_buffer = ""
        self._live = None
        self._loading_active = False
        self._loading_task = None

    def _stop_live(self) -> None:
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

    def start_loading(self, message: str = None) -> None:
        """Starts the visual processing indicator (animated via asyncio with static fallback)."""
        self._stop_live()
        self.stop_loading()
        
        if message is None:
            message = i18n.t("console_io", "thinking")
        
        # Remove trailing periods from the message so the animation controls the flow of dots
        message = message.rstrip(".")
        self._loading_active = True
        try:
            self._loading_task = asyncio.create_task(self._animate_loading(message))
        except RuntimeError:
            print(f"{Fore.GREEN}{Style.BRIGHT}{message}...{Style.RESET_ALL}", end="", flush=True)
            self._loading_task = None

    async def _animate_loading(self, message: str) -> None:
        """Coroutine that animates the growing loading dots."""
        dots = 0
        try:
            while self._loading_active:
                dots_str = "." * dots + " " * (3 - dots)
                print(f"\r{Fore.GREEN}{Style.BRIGHT}{message}{dots_str}{Style.RESET_ALL}", end="", flush=True)
                await asyncio.sleep(0.5)
                dots = (dots + 1) % 4
        except asyncio.CancelledError:
            pass

    def stop_loading(self) -> None:
        """Stops the visual processing indicator and clears the line."""
        if self._loading_active:
            self._loading_active = False
            if self._loading_task:
                self._loading_task.cancel()
                self._loading_task = None
            # Clear the line by overwriting it with spaces using carriage return
            print("\r" + " " * 40 + "\r", end="", flush=True)

    def write_thought(self, text: str) -> None:
        self.stop_loading()
        self._stop_live()
        # Thoughts in dim/italic tone using rich
        self._console.print(f"[dim]{text}[/dim]", end="", highlight=False)

    def write_text(self, text: str) -> None:
        self.stop_loading()
        if self._first_text:
            self._console.print(f"\n[bold magenta]AntGravity > [/bold magenta]")
            self._first_text = False
            self._text_buffer = ""
            # Initializes real-time (Live) Markdown rendering
            self._live = Live(Markdown(self._text_buffer), console=self._console, auto_refresh=True)
            self._live.start()
        
        self._text_buffer += text
        if self._live:
            self._live.update(Markdown(self._text_buffer))

    def write_tool_call(self, name: str, args: dict) -> None:
        self.stop_loading()
        self._stop_live()
        self._console.print(f"\n[yellow]{i18n.t('console_io', 'tool_calling', name=name, args=args)}[/yellow]")

    def write_tool_result(self, name: str, result: str, error: str = None) -> None:
        self.stop_loading()
        self._stop_live()
        if error:
            self._console.print(f"\n[red]{i18n.t('console_io', 'tool_error', name=name, error=error)}[/red]")
        else:
            self._console.print(f"\n[blue]{i18n.t('console_io', 'tool_result', name=name, result=result)}[/blue]")

    def reset(self) -> None:
        """Resets the writer state for a new text stream."""
        self.stop_loading()
        self._stop_live()
        self._first_text = True
        self._text_buffer = ""


class ConsoleInputReader(InputReader):
    """Concrete terminal input reader using input() or prompt_toolkit (SRP)."""
    def __init__(self):
        self._session = None

    async def read_input(self, prompt_text: str, suggestions: list[str] = None, file_suggestions: list[str] = None) -> str:
        prompt_with_color = f"\n{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        
        if HAS_PROMPT_TOOLKIT and (suggestions or file_suggestions):
            try:
                # Initialize the session on-demand to avoid failure during instantiation in tests or CI/CD
                if self._session is None:
                    self._session = PromptSession()
                
                completer = AntCompleter(
                    command_suggestions=suggestions or [],
                    file_suggestions=file_suggestions or []
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
