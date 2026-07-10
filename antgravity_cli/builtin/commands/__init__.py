from .exit import ExitCommand
from .reset import ResetCommand
from .help import HelpCommand
from .ants import AntsCommand
from .disable_skill import DisableSkillCommand
from .enable_skill import EnableSkillCommand
from .disable_agent import DisableAgentCommand
from .enable_agent import EnableAgentCommand
from .reload import ReloadCommand
from .clear import ClearCommand
from .history import HistoryCommand
from .save import SaveCommand
from .load import LoadCommand
from .config import ConfigCommand

COMMANDS = [
    ExitCommand(),
    ResetCommand(),
    HelpCommand(),
    AntsCommand(),
    DisableSkillCommand(),
    EnableSkillCommand(),
    DisableAgentCommand(),
    EnableAgentCommand(),
    ReloadCommand(),
    ClearCommand(),
    HistoryCommand(),
    SaveCommand(),
    LoadCommand(),
    ConfigCommand()
]

def discover_custom_commands(workspaces) -> list:
    """Discovers and imports custom REPLCommand classes from workspace/.agents/commands/ directories."""
    import os
    import importlib.util
    import inspect
    from .base import REPLCommand

    custom_commands = []
    if not workspaces:
        return []

    for ws in workspaces:
        custom_cmd_dir = os.path.abspath(os.path.join(ws, ".agents", "commands"))
        if not os.path.isdir(custom_cmd_dir):
            continue

        for entry in os.listdir(custom_cmd_dir):
            if entry.endswith(".py") and not entry.startswith("__"):
                module_path = os.path.join(custom_cmd_dir, entry)
                module_name = f"antgravity_custom_command_{os.path.splitext(entry)[0]}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, REPLCommand) and obj is not REPLCommand:
                                custom_commands.append(obj())
                except Exception:
                    # Silently ignore load errors
                    pass
    return custom_commands

def get_command_map(workspaces=None):
    """Returns a dictionary mapping command trigger strings to their REPLCommand instance, including custom plugins."""
    cmd_map = {}
    for cmd in COMMANDS:
        for trigger in cmd.triggers:
            cmd_map[trigger] = cmd
            
    if workspaces:
        for cmd in discover_custom_commands(workspaces):
            for trigger in cmd.triggers:
                cmd_map[trigger] = cmd
    return cmd_map

def get_command_triggers(workspaces=None) -> list[str]:
    """Returns a list of all registered trigger strings, including custom plugins."""
    triggers = []
    for cmd in COMMANDS:
        triggers.extend(cmd.triggers)
    if workspaces:
        for cmd in discover_custom_commands(workspaces):
            triggers.extend(cmd.triggers)
    return sorted(list(set(triggers)))
