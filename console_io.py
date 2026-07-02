import asyncio
import colorama
from colorama import Fore, Style
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from interfaces import OutputWriter, InputReader

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import ANSI
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# Inicializa colorama para suporte de cores no console (especialmente Windows)
colorama.init()

class ConsoleOutputWriter(OutputWriter):
    """Implementação concreta de escrita no terminal usando colorama e rich para Markdown (SRP)."""
    def __init__(self):
        self._first_text = True
        self._console = Console(force_terminal=True)
        self._text_buffer = ""
        self._live = None
        self._loading_status = None

    def _stop_live(self) -> None:
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

    def start_loading(self, message: str = "Pensando") -> None:
        """Inicia o indicador visual de processamento (animado via asyncio com fallback estático)."""
        self._stop_live()
        self.stop_loading()
        
        # Remove pontos no final do message para que a animação controle o fluxo de pontinhos
        message = message.rstrip(".")
        self._loading_active = True
        try:
            self._loading_task = asyncio.create_task(self._animate_loading(message))
        except RuntimeError:
            print(f"{Fore.GREEN}{Style.BRIGHT}{message}...{Style.RESET_ALL}", end="", flush=True)
            self._loading_task = None

    async def _animate_loading(self, message: str) -> None:
        """Corrotina que anima a exibição de pontinhos crescentes de carregamento."""
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
        """Encerra o indicador visual de processamento limpando a linha."""
        if getattr(self, '_loading_active', False):
            self._loading_active = False
            if hasattr(self, '_loading_task') and self._loading_task:
                self._loading_task.cancel()
                self._loading_task = None
            # Limpa a palavra imprimindo espaços por cima usando retorno de carro
            print("\r" + " " * 40 + "\r", end="", flush=True)

    def write_thought(self, text: str) -> None:
        self.stop_loading()
        self._stop_live()
        # Pensamentos em tom cinza/itálico usando rich
        self._console.print(f"[dim]{text}[/dim]", end="", highlight=False)

    def write_text(self, text: str) -> None:
        self.stop_loading()
        if self._first_text:
            self._console.print(f"\n[bold magenta]Antigravity > [/bold magenta]")
            self._first_text = False
            self._text_buffer = ""
            # Inicializa a renderização em tempo real (Live) do Markdown
            self._live = Live(Markdown(self._text_buffer), console=self._console, auto_refresh=True)
            self._live.start()
        
        self._text_buffer += text
        if self._live:
            self._live.update(Markdown(self._text_buffer))

    def write_tool_call(self, name: str, args: dict) -> None:
        self.stop_loading()
        self._stop_live()
        self._console.print(f"\n[yellow][Ferramenta] Chamando: {name} com {args}[/yellow]")

    def write_tool_result(self, name: str, result: str, error: str = None) -> None:
        self.stop_loading()
        self._stop_live()
        if error:
            self._console.print(f"\n[red][Ferramenta] Erro em {name}: {error}[/red]")
        else:
            self._console.print(f"\n[blue][Ferramenta] Resultado de {name}: {result}[/blue]")

    def reset(self) -> None:
        """Reseta o estado do escritor para nova stream de texto."""
        self.stop_loading()
        self._stop_live()
        self._first_text = True
        self._text_buffer = ""


class ConsoleInputReader(InputReader):
    """Implementação concreta de leitura do terminal usando input() ou prompt_toolkit (SRP)."""
    def __init__(self):
        self._session = None

    async def read_input(self, prompt_text: str, suggestions: list[str] = None) -> str:
        prompt_with_color = f"\n{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        
        if HAS_PROMPT_TOOLKIT and suggestions:
            try:
                # Inicializa a sessão sob demanda para não falhar na instanciação em testes ou CI/CD
                if self._session is None:
                    self._session = PromptSession()
                
                completer = WordCompleter(suggestions, ignore_case=True)
                # Usa a sessão assíncrona do prompt_toolkit integrada ao asyncio
                return (await self._session.prompt_async(ANSI(prompt_with_color), completer=completer)).strip()
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # Fallback seguro para input() nativo em qualquer caso de erro do prompt_toolkit (ex: NoConsoleScreenBufferError)
                return input(prompt_with_color).strip()
        else:
            return input(prompt_with_color).strip()
