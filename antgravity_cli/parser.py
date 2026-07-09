import os
import re
from typing import Tuple, List
from . import i18n
from .interfaces import DirectiveProcessor

class FileDirectiveProcessor(DirectiveProcessor):
    """File and folder directive processor with the '@' prefix (SRP/OCP/LSP)."""
    
    def process(self, prompt: str, skills_paths: list[str] = None) -> Tuple[str, list[str]]:
        extra_context = []
        # Accepts @[path with spaces] or @path_without_spaces (avoids emails)
        file_matches = re.finditer(r'(?<!\w)@(?:\[([^\]]+)\]|([^\s\x00-\x1F\x7F]+))', prompt)
        files_to_inject = []
        for match in file_matches:
            path = match.group(1) or match.group(2)
            # Clean common punctuation at the end of the path without brackets
            if not match.group(1):
                path = re.sub(r'[.,;:!?)]+$', '', path)
            files_to_inject.append(path)

        for filepath in files_to_inject:
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    extra_context.append(f"{i18n.t('parser', 'file_content_header', filename=os.path.basename(filepath), filepath=filepath)}\n{content}\n")
                except Exception as e:
                    extra_context.append(f"{i18n.t('parser', 'error_reading_file', filepath=filepath, error=str(e))}\n")
            elif os.path.isdir(filepath):
                try:
                    entries = os.listdir(filepath)
                    content = "\n".join(entries)
                    extra_context.append(f"{i18n.t('parser', 'directory_listing_header', filepath=filepath)}\n{content}\n")
                except Exception as e:
                    extra_context.append(f"{i18n.t('parser', 'error_listing_directory', filepath=filepath, error=str(e))}\n")
                    
        return prompt, extra_context


class SkillDirectiveProcessor(DirectiveProcessor):
    """Skill directive processor with the '/' prefix (SRP/OCP/LSP)."""
    
    def process(self, prompt: str, skills_paths: list[str] = None) -> Tuple[str, list[str]]:
        extra_context = []
        # Ignores special REPL commands (/exit, /quit, /reset)
        skill_matches = re.finditer(r'(?<!\w)/([a-zA-Z0-9_-]+)', prompt)
        skills_to_inject = []
        for match in skill_matches:
            skill_name = match.group(1)
            if skill_name in ("exit", "quit", "reset"):
                continue
            skills_to_inject.append(skill_name)

        from .list_skills import discover_skills_in_paths

        for skill_name in skills_to_inject:
            paths_to_search = list(skills_paths) if skills_paths else []
            if not paths_to_search:
                from .utils import get_base_path
                base_dir = get_base_path()
                cli_skills_dir = os.path.join(base_dir, "builtin", "skills")
                paths_to_search = ["skills", ".agents/skills", cli_skills_dir]
            
            # Unified dry discovery check
            if skill_name in discover_skills_in_paths(paths_to_search):
                for base_path in paths_to_search:
                    skill_dir = os.path.join(base_path, skill_name)
                    skill_md_path = os.path.join(skill_dir, "SKILL.md")
                    if os.path.isfile(skill_md_path):
                        try:
                            with open(skill_md_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            extra_context.append(f"{i18n.t('parser', 'skill_instructions_header', skill_name=skill_name)}\n{content}\n")
                            break
                        except Exception as e:
                            extra_context.append(f"{i18n.t('parser', 'error_loading_skill', skill_name=skill_name, error=str(e))}\n")
                        
        return prompt, extra_context


class PromptPreprocessor:
    """Orchestrator for prompt preprocessing (SRP/OCP)."""
    
    def __init__(self, processors: list[DirectiveProcessor] = None):
        self._processors = processors if processors is not None else [
            FileDirectiveProcessor(),
            SkillDirectiveProcessor()
        ]

    def preprocess(self, prompt: str, skills_paths: list[str] = None) -> str:
        aggregated_context = []
        current_prompt = prompt
        for processor in self._processors:
            current_prompt, extra_context = processor.process(current_prompt, skills_paths)
            aggregated_context.extend(extra_context)
            
        if aggregated_context:
            return current_prompt + "\n\n" + "\n".join(aggregated_context)
        return current_prompt


# Functional compatibility wrapper
def preprocess_prompt(prompt: str, skills_paths: list[str] = None) -> str:
    """Functional wrapper compatible with previous versions."""
    return PromptPreprocessor().preprocess(prompt, skills_paths)
