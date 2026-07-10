import os
import re
from typing import Tuple
import click
from colorama import Fore, Style
from .. import i18n
from ..interfaces import DirectiveProcessor

class FileDirectiveProcessor(DirectiveProcessor):
    """File and folder directive processor with the '@' prefix (SRP/OCP/LSP)."""
    
    def process(self, prompt: str, skills_paths: list[str] | None = None, disabled_skills: set[str] | None = None) -> Tuple[str, list[str]]:
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
            else:
                click.echo(f"{Fore.YELLOW}[WARNING] {i18n.t('parser', 'file_not_found_warning', filepath=filepath)}{Style.RESET_ALL}", err=True)
                    
        return prompt, extra_context
