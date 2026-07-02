import colorama
from colorama import Fore, Style

# Inicializa colorama para suporte de cores no console (especialmente Windows)
colorama.init()

def cli_ask_user_handler(tool_call) -> bool:
    """Manipulador para solicitar aprovação do usuário no terminal no modo seguro."""
    print(f"\n{Fore.LIGHTYELLOW_EX}[?] O agente deseja executar a ferramenta: {Fore.WHITE}{tool_call.name}{Style.RESET_ALL}")
    print(f"    Argumentos: {tool_call.args}")
    try:
        ans = input(f"{Fore.CYAN}    Permitir execução? [y/N]: {Style.RESET_ALL}").strip().lower()
        return ans in ('y', 'yes', 'sim', 's')
    except (KeyboardInterrupt, EOFError):
        print("\n    Negado por interrupção.")
        return False
