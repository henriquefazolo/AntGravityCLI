import os
import re
from typing import Tuple
from .. import i18n
from ..interfaces import DirectiveProcessor

class SkillDirectiveProcessor(DirectiveProcessor):
    """Skill directive processor with the '/' prefix (SRP/OCP/LSP)."""
    
    def process(self, prompt: str, skills_paths: list[str] = None, disabled_skills: set[str] = None) -> Tuple[str, list[str]]:
        extra_context = []
        # Ignores special REPL commands dynamically
        from ..builtin.commands import get_command_map
        commands_map = get_command_map()
        
        skill_matches = re.finditer(r'(?<!\w)/([a-zA-Z0-9_-]+)', prompt)
        skills_to_inject = []
        for match in skill_matches:
            skill_name = match.group(1)
            if f"/{skill_name}" in commands_map:
                continue
            if disabled_skills and skill_name in disabled_skills:
                continue
            skills_to_inject.append(skill_name)

        from ..list_skills import discover_skills_in_paths

        for skill_name in skills_to_inject:
            paths_to_search = list(skills_paths) if skills_paths else []
            if not paths_to_search:
                from ..utils import get_base_path
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
