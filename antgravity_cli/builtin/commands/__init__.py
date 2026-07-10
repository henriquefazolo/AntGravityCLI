from .exit import ExitCommand
from .reset import ResetCommand
from .help import HelpCommand
from .ants import AntsCommand
from .disable_skill import DisableSkillCommand
from .enable_skill import EnableSkillCommand
from .disable_agent import DisableAgentCommand
from .enable_agent import EnableAgentCommand

COMMANDS = [
    ExitCommand(),
    ResetCommand(),
    HelpCommand(),
    AntsCommand(),
    DisableSkillCommand(),
    EnableSkillCommand(),
    DisableAgentCommand(),
    EnableAgentCommand()
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
