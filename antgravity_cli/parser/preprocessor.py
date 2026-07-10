from ..interfaces import DirectiveProcessor
from .file_processor import FileDirectiveProcessor
from .skill_processor import SkillDirectiveProcessor

class PromptPreprocessor:
    """Orchestrator for prompt preprocessing (SRP/OCP)."""
    
    def __init__(self, processors: list[DirectiveProcessor] = None):
        self._processors = processors if processors is not None else [
            FileDirectiveProcessor(),
            SkillDirectiveProcessor()
        ]

    def preprocess(self, prompt: str, skills_paths: list[str] = None, disabled_skills: set[str] = None) -> str:
        aggregated_context = []
        current_prompt = prompt
        for processor in self._processors:
            if isinstance(processor, SkillDirectiveProcessor):
                current_prompt, extra_context = processor.process(current_prompt, skills_paths, disabled_skills=disabled_skills)
            else:
                current_prompt, extra_context = processor.process(current_prompt, skills_paths)
            aggregated_context.extend(extra_context)
            
        if aggregated_context:
            return current_prompt + "\n\n" + "\n".join(aggregated_context)
        return current_prompt


def preprocess_prompt(prompt: str, skills_paths: list[str] = None, disabled_skills: set[str] = None) -> str:
    """Functional wrapper compatible with previous versions."""
    return PromptPreprocessor().preprocess(prompt, skills_paths, disabled_skills=disabled_skills)
