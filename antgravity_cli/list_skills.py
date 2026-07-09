import os
from . import i18n

def discover_skills_in_paths(paths: list[str]) -> list[str]:
    """Scans the provided directories for subfolders containing a SKILL.md file and returns sorted skill names."""
    skills = []
    if not paths:
        return []
    for path in paths:
        if path and os.path.exists(path) and os.path.isdir(path):
            try:
                for entry in os.listdir(path):
                    entry_path = os.path.join(path, entry)
                    if os.path.isdir(entry_path):
                        if os.path.exists(os.path.join(entry_path, "SKILL.md")):
                            skills.append(entry)
            except Exception:
                pass
    return sorted(list(set(skills)))

def get_skills() -> list[str]:
    """Returns a sorted list of directory names inside builtin/skills."""
    from .utils import get_base_path
    base_dir = get_base_path()
    skills_dir = os.path.join(base_dir, "builtin", "skills")
    return discover_skills_in_paths([skills_dir])

def main() -> None:
    """Lists the names of the directories (skills) located in .agents/skills."""
    # Resolve the active language from ANTGRAVITY_LANG env var if present
    lang = os.environ.get("ANTGRAVITY_LANG", "en-us")
    i18n.set_language(lang)

    # Path to the local agent skills directory
    from .utils import get_base_path
    base_dir = get_base_path()
    skills_dir = os.path.join(base_dir, "builtin", "skills")

    if not os.path.isdir(skills_dir):
        print(i18n.t("list_skills", "directory_not_found", directory=skills_dir))
        return

    skills = get_skills()
    if not skills:
        print(i18n.t("list_skills", "no_skills_found"))
        return

    print(i18n.t("list_skills", "skills_header"))
    for skill in skills:
        print(f"  - {skill}")

if __name__ == "__main__":
    main()
