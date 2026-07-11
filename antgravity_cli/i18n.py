import os
import json
import contextvars
from typing import Dict, Any, Optional

_current_language = contextvars.ContextVar("current_language", default="en-us")
_translation_cache: contextvars.ContextVar[Optional[Dict[str, Dict[str, str]]]] = contextvars.ContextVar("translation_cache", default=None)

def _get_cache() -> Dict[str, Dict[str, str]]:
    cache = _translation_cache.get()
    if cache is None:
        cache = {}
        _translation_cache.set(cache)
    return cache

def set_language(lang: str) -> None:
    """Sets the active language for CLI output messages."""
    if lang:
        _current_language.set(lang.lower().strip())
        _translation_cache.set({})

def get_language() -> str:
    """Returns the currently active language code."""
    return _current_language.get()

def _load_translations(lang: str, module: str) -> Dict[str, str]:
    """Loads translations from translate/{lang}/{module}.json with caching."""
    cache_key = f"{lang}/{module}"
    cache = _get_cache()
    if cache_key in cache:
        return cache[cache_key]

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
            
    new_cache = dict(cache)
    new_cache[cache_key] = translations
    _translation_cache.set(new_cache)
    return translations

def t(module: str, key: str, **kwargs: Any) -> str:
    """
    Returns the translated string for a given module and key.
    Falls back to en-us if the key is missing in the current language, 
    and returns the key itself if not found anywhere.
    """
    current_lang = _current_language.get()
    # 1. Try to get translation in active language
    lang_translations = _load_translations(current_lang, module)
    message = lang_translations.get(key)

    # 2. Fall back to en-us if not found and current is not en-us
    if message is None and current_lang != "en-us":
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
                f"Translation formatting failed for key '{module}.{key}' (lang: '{current_lang}'). "
                f"Format arguments mismatch. Error: {e}",
                UserWarning,
                stacklevel=2
            )

    return message
