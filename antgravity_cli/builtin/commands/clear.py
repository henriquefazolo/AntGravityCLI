import os
import click
from .base import REPLCommand

class ClearCommand(REPLCommand):
    """Command that clears the terminal screen (cross-platform)."""

    @property
    def triggers(self) -> list[str]:
        return ["/clear", "/cls"]

    @property
    def description_key(self) -> str:
        return "command_clear_desc"

    async def execute(self, agent, context=None) -> bool:
        os.system("cls" if os.name == "nt" else "clear")
        return True
