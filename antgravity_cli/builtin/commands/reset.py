import click
from antgravity_cli import i18n
from .base import REPLCommand

class ResetCommand(REPLCommand):
    """Command that clears the active interactive session's conversation history."""

    @property
    def triggers(self) -> list[str]:
        return ["/reset"]

    @property
    def description_key(self) -> str:
        return "command_reset_desc"

    async def execute(self, agent, context=None) -> bool:
        agent.conversation.clear_history()
        click.echo(i18n.t("repl", "conversation_history_cleared"))
        return True
