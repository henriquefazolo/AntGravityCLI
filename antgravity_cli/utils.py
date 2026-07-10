import os
import sys

def get_base_path() -> str:
    """Returns the base path of the project, compatible with PyInstaller standalone executable format."""
    if getattr(sys, 'frozen', False):
        # PyInstaller temp folder where execution assets are unpacked
        return sys._MEIPASS
    # Normal execution, resolve folder relative to utils.py location
    return os.path.dirname(os.path.abspath(__file__))


def get_workspace_files_and_folders(workspace_path: str, max_depth: int = 4) -> list[str]:
    """Recursively list all files and folders in the workspace up to max_depth, excluding ignored folders."""
    ignored_dirs = {
        '.git', '.venv', 'venv', '__pycache__', '.idea', '.vscode',
        '.pytest_cache', 'build', 'dist', 'node_modules'
    }
    ignored_extensions = {'.pyc', '.pyo', '.pyd'}

    suggestions = []
    workspace_path = os.path.abspath(workspace_path)
    if not os.path.isdir(workspace_path):
        return []

    base_depth = workspace_path.count(os.path.sep)

    for root, dirs, files in os.walk(workspace_path):
        # Calculate depth relative to workspace root
        current_depth = root.count(os.path.sep) - base_depth
        if current_depth >= max_depth:
            dirs[:] = []  # stop recursing deeper
            continue

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


def get_history_file_path() -> str:
    """Returns the platform-specific standard location for the history file.
    
    - Windows: %LOCALAPPDATA%\AntGravity\history
    - macOS: ~/Library/Application Support/AntGravity/history
    - Linux: ~/.local/share/antgravity/history (or $XDG_DATA_HOME/antgravity/history)
    """
    home = os.path.expanduser("~")
    
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        history_dir = os.path.join(local_app_data, "AntGravity")
    elif sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        if app_data:
            history_dir = os.path.join(app_data, "AntGravity")
        else:
            history_dir = os.path.join(home, ".antgravity")
    elif sys.platform == "darwin":
        history_dir = os.path.join(home, "Library", "Application Support", "AntGravity")
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            history_dir = os.path.join(xdg_data, "antgravity")
        else:
            history_dir = os.path.join(home, ".local", "share", "antgravity")

    try:
        os.makedirs(history_dir, exist_ok=True)
    except Exception:
        return os.path.join(home, ".antgravity_history")

    return os.path.join(history_dir, "history")


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """Parses YAML frontmatter from markdown content.
    
    Returns a tuple of (metadata_dict, body_content).
    """
    import re
    import yaml
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content.strip()
    yaml_block = match.group(1)
    body = match.group(2).strip()
    try:
        parsed_yaml = yaml.safe_load(yaml_block) or {}
    except Exception:
        parsed_yaml = {}
    return parsed_yaml, body
