import colorama
from colorama import Fore, Style

from . import i18n

# Initialize colorama for console color support (especially Windows)
colorama.init()

def cli_ask_user_handler(tool_call) -> bool:
    """Handler to request user approval in the terminal in safe mode."""
    print(f"\n{Fore.LIGHTYELLOW_EX}{i18n.t('handlers', 'agent_wants_to_execute', name=tool_call.name)}{Style.RESET_ALL}")
    print(f"{i18n.t('handlers', 'arguments', args=tool_call.args)}")
    try:
        ans = input(f"{Fore.CYAN}{i18n.t('handlers', 'allow_execution')}{Style.RESET_ALL}").strip().lower()
        return ans in ('y', 'yes', 'sim', 's')
    except (KeyboardInterrupt, EOFError):
        print(f"\n{i18n.t('handlers', 'denied_by_interruption')}")
        return False
