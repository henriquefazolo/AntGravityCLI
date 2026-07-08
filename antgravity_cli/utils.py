import os
import sys

def get_base_path() -> str:
    """Returns the base path of the project, compatible with PyInstaller standalone executable format."""
    if getattr(sys, 'frozen', False):
        # PyInstaller temp folder where execution assets are unpacked
        return sys._MEIPASS
    # Normal execution, resolve folder relative to utils.py location
    return os.path.dirname(os.path.abspath(__file__))


def get_workspace_files_and_folders(workspace_path: str) -> list[str]:
    """Recursively list all files and folders in the workspace, excluding ignored folders."""
    ignored_dirs = {
        '.git', '.venv', 'venv', '__pycache__', '.idea', '.vscode',
        '.pytest_cache', 'build', 'dist', 'node_modules'
    }
    ignored_extensions = {'.pyc', '.pyo', '.pyd'}

    suggestions = []
    workspace_path = os.path.abspath(workspace_path)
    if not os.path.isdir(workspace_path):
        return []

    for root, dirs, files in os.walk(workspace_path):
        # Modify dirs in-place to avoid walking down ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith('.egg-info')]

        for d in dirs:
            full_path = os.path.join(root, d)
            rel_path = os.path.relpath(full_path, workspace_path)
            # Normalize to forward slashes
            rel_path_formatted = rel_path.replace(os.path.sep, '/') + '/'
            suggestions.append(rel_path_formatted)

        for f in files:
            _, ext = os.path.splitext(f)
            if ext in ignored_extensions:
                continue
            if f.endswith('.egg-info'):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, workspace_path)
            # Normalize to forward slashes
            rel_path_formatted = rel_path.replace(os.path.sep, '/')
            suggestions.append(rel_path_formatted)

    return sorted(suggestions)
