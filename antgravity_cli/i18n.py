import os
import json
from typing import Dict, Any

_current_language = "en-us"
_translation_cache: Dict[str, Dict[str, str]] = {}

def set_language(lang: str) -> None:
    """Sets the active language for CLI output messages."""
    global _current_language
    if lang:
        _current_language = lang.lower().strip()

def get_language() -> str:
    """Returns the currently active language code."""
    return _current_language

def _load_translations(lang: str, module: str) -> Dict[str, str]:
    """Loads translations from translate/{lang}/{module}.json with caching."""
    cache_key = f"{lang}/{module}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    # Resolve translations directory relative to this file, compatible with PyInstaller
    from .utils import get_base_path
    base_dir = get_base_path()
    json_path = os.path.join(base_dir, "translate", lang, f"{module}.json")

    translations = {}
    if os.path.isfile(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                translations = json.load(f)
        except Exception:
            # Fallback to empty dict on load errors
            translations = {}
            
    _translation_cache[cache_key] = translations
    return translations

def t(module: str, key: str, **kwargs: Any) -> str:
    """
    Returns the translated string for a given module and key.
    Falls back to en-us if the key is missing in the current language, 
    and returns the key itself if not found anywhere.
    """
    # 1. Try to get translation in active language
    lang_translations = _load_translations(_current_language, module)
    message = lang_translations.get(key)

    # 2. Fall back to en-us if not found and current is not en-us
    if message is None and _current_language != "en-us":
        en_translations = _load_translations("en-us", module)
        message = en_translations.get(key)

    # 3. Fall back to the key itself if still not found
    if message is None:
        message = key

    # 4. Format string if arguments are passed
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError, IndexError) as e:
            import warnings
            warnings.warn(
                f"Translation formatting failed for key '{module}.{key}' (lang: '{_current_language}'). "
                f"Format arguments mismatch. Error: {e}",
                UserWarning,
                stacklevel=2
            )

    return message
