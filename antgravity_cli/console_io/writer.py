import asyncio
import colorama
from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from ..interfaces import OutputWriter
from .. import i18n

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
