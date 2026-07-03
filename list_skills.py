import os
import i18n

def get_skills() -> list[str]:
    """Returns a sorted list of directory names inside .agents/skills."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(base_dir, ".agents", "skills")
    if not os.path.isdir(skills_dir):
        return []
    try:
        entries = os.listdir(skills_dir)
        skills = [entry for entry in entries if os.path.isdir(os.path.join(skills_dir, entry))]
        return sorted(skills)
    except Exception:
        return []

def main() -> None:
    """Lists the names of the directories (skills) located in .agents/skills."""
    # Resolve the active language from ANTGRAVITY_LANG env var if present
    lang = os.environ.get("ANTGRAVITY_LANG", "en-us")
    i18n.set_language(lang)

    # Path to the local agent skills directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(base_dir, ".agents", "skills")

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
