from .exit import ExitCommand
from .reset import ResetCommand

COMMANDS = [
    ExitCommand(),
    ResetCommand()
]

def get_command_map():
    """Returns a dictionary mapping command trigger strings to their REPLCommand instance."""
    cmd_map = {}
    for cmd in COMMANDS:
        for trigger in cmd.triggers:
            cmd_map[trigger] = cmd
    return cmd_map

def get_command_triggers() -> list[str]:
    """Returns a list of all registered trigger strings."""
    triggers = []
    for cmd in COMMANDS:
        triggers.extend(cmd.triggers)
    return sorted(list(set(triggers)))
