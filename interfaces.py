from abc import ABC, abstractmethod
from typing import Tuple, List

class DirectiveProcessor(ABC):
    """Base interface for prompt directive processors (LSP/OCP)."""
    @abstractmethod
    def process(self, prompt: str, skills_paths: list[str] = None) -> Tuple[str, list[str]]:
        """
        Processes the prompt and returns a tuple containing the updated prompt and a list
        of strings containing the extra context to be injected.
        """
        pass

class OutputWriter(ABC):
    """Base interface for agent communication outputs (DIP/ISP)."""
    @abstractmethod
    def write_thought(self, text: str) -> None:
        pass

    @abstractmethod
    def write_text(self, text: str) -> None:
        pass

    @abstractmethod
    def write_tool_call(self, name: str, args: dict) -> None:
        pass

    @abstractmethod
    def write_tool_result(self, name: str, result: str, error: str = None) -> None:
        pass

    def start_loading(self, message: str = "Thinking...") -> None:
        """Starts a visual processing indicator (optional)."""
        pass

    def stop_loading(self) -> None:
        """Stops the visual processing indicator (optional)."""
        pass

class InputReader(ABC):
    """Base interface for user text input (DIP/ISP)."""
    @abstractmethod
    async def read_input(self, prompt_text: str, suggestions: list[str] = None) -> str:
        pass
