import unittest
from unittest.mock import patch
import os
import tempfile
import shutil

from antgravity_cli.parser import preprocess_prompt, PromptPreprocessor
from antgravity_cli.interfaces import DirectiveProcessor


class TestAntigravityParser(unittest.TestCase):
    def test_preprocess_prompt_file_injection(self):
        """Verify that references to @file are injected with the file content."""
        temp_file = "temp_test_file.txt"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("Temporary file test content.")
            
            prompt = f"Analise o arquivo @{temp_file} por favor."
            processed = preprocess_prompt(prompt)
            
            self.assertIn("=== FILE CONTENT: temp_test_file.txt", processed)
            self.assertIn("Temporary file test content.", processed)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_preprocess_prompt_skill_injection(self):
        """Verify that references to /skill are injected with the rules from SKILL.md."""
        temp_skills_dir = "temp_skills"
        temp_skill_name = "test_skill"
        skill_dir = os.path.join(temp_skills_dir, temp_skill_name)
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        
        try:
            os.makedirs(skill_dir, exist_ok=True)
            with open(skill_md_path, "w", encoding="utf-8") as f:
                f.write("---\nname: Test Skill\ndescription: Test description\n---\nRegras da skill de teste.")
                
            prompt = f"Use a skill /{temp_skill_name} para rodar."
            processed = preprocess_prompt(prompt, skills_paths=[temp_skills_dir])
            
            self.assertIn("=== SKILL INSTRUCTIONS: test_skill", processed)
            self.assertIn("Regras da skill de teste.", processed)
        finally:
            if os.path.exists(skill_md_path):
                os.remove(skill_md_path)
            if os.path.exists(skill_dir):
                os.rmdir(skill_dir)
            if os.path.exists(temp_skills_dir):
                os.rmdir(temp_skills_dir)

    def test_prompt_preprocessor_ocp_extensibility(self):
        """Verify that new directive processors can be added without modifying existing code (OCP)."""
        import re
        
        class MockIssueDirectiveProcessor(DirectiveProcessor):
            def process(self, prompt: str, skills_paths=None, disabled_skills=None):
                match = re.search(r'#issue-(\d+)', prompt)
                extra = []
                if match:
                    issue_id = match.group(1)
                    extra.append(f"=== ISSUE #{issue_id} DETAILS ===\nCorrigir bug de login no sistema.")
                return prompt, extra

        preprocessor = PromptPreprocessor(processors=[MockIssueDirectiveProcessor()])
        
        prompt = "Resolva a issue #issue-999"
        processed = preprocessor.preprocess(prompt)
        
        self.assertIn("=== ISSUE #999 DETAILS ===", processed)
        self.assertIn("Corrigir bug de login no sistema.", processed)

    def test_preprocess_prompt_excludes_disabled_skills(self):
        """Verify that preprocess_prompt does not load instructions for a disabled skill."""
        tmp_dir = tempfile.mkdtemp()
        skill_dir = os.path.join(tmp_dir, "test_skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("Secret Instructions")
            
        try:
            # When active/enabled:
            prompt1 = preprocess_prompt("Please run /test_skill", skills_paths=[tmp_dir])
            self.assertIn("Secret Instructions", prompt1)
            
            # When disabled:
            prompt2 = preprocess_prompt("Please run /test_skill", skills_paths=[tmp_dir], disabled_skills={"test_skill"})
            self.assertNotIn("Secret Instructions", prompt2)
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    unittest.main()
