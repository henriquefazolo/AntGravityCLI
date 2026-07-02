from abc import ABC, abstractmethod
from typing import Tuple, List

class DirectiveProcessor(ABC):
    """Interface base para processadores de diretivas em prompts (LSP/OCP)."""
    @abstractmethod
    def process(self, prompt: str, skills_paths: list[str] = None) -> Tuple[str, list[str]]:
        """
        Processa o prompt e retorna uma tupla com o prompt atualizado e uma lista
        de strings contendo o contexto extra a ser injetado.
        """
        pass

class OutputWriter(ABC):
    """Interface base para saídas de comunicação do agente (DIP/ISP)."""
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

    def start_loading(self, message: str = "Pensando...") -> None:
        """Inicia um indicador visual de processamento (opcional)."""
        pass

    def stop_loading(self) -> None:
        """Para o indicador visual de processamento (opcional)."""
        pass

class InputReader(ABC):
    """Interface base para entrada de texto do usuário (DIP/ISP)."""
    @abstractmethod
    async def read_input(self, prompt_text: str, suggestions: list[str] = None) -> str:
        pass
