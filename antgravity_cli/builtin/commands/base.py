from abc import ABC, abstractmethod

class REPLCommand(ABC):
    """Base interface for all CLI interactive session REPL commands."""

    @property
    @abstractmethod
    def triggers(self) -> list[str]:
        """Returns the list of string triggers that activate this command (e.g. ['/exit', '/quit'])."""
        pass

    @property
    @abstractmethod
    def description_key(self) -> str:
        """Returns the i18n translation key describing the command's purpose."""
        pass

    @abstractmethod
    async def execute(self, agent, context=None) -> bool:
        """Executes the command logic.
        
        Args:
            agent: The active LocalAgent instance.
            context: Optional context information.
            
        Returns:
            bool: True if the REPL session should continue, False to terminate the REPL.
        """
        pass
