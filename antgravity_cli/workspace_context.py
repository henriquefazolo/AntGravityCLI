"""Centralized workspace context for discovery of skills, subagents, and paths."""

import os
from typing import List, Optional, Dict, Any

from google.antigravity.types import SubagentConfig


class WorkspaceContext:
    """Centralized registry that resolves and caches workspace discovery results.

    This eliminates the duplicated discovery logic previously scattered across
    config.py, repl.py, help.py, ants.py, disable_agent.py, and disable_skill.py.
    """

    def __init__(self, workspaces: Optional[List[str]] = None, skills_paths: Optional[List[str]] = None):
        self._workspaces = [os.path.abspath(w) for w in workspaces] if workspaces else [os.path.abspath(".")]
        self._skills_paths = skills_paths or []
        self._subagent_cache: Optional[List[SubagentConfig]] = None
        self._skills_cache: Optional[List[str]] = None
        self._commands_cache: Optional[Dict[str, Any]] = None

    @property
    def workspaces(self) -> List[str]:
        """Returns the list of resolved absolute workspace paths."""
        return self._workspaces

    @property
    def skills_paths(self) -> List[str]:
        """Returns the list of resolved skills paths."""
        return self._skills_paths

    @skills_paths.setter
    def skills_paths(self, value: List[str]) -> None:
        """Sets the skills paths and invalidates the cache."""
        self._skills_paths = value or []
        self._skills_cache = None

    def get_subagent_search_paths(self) -> List[str]:
        """Returns the list of subagent search directories derived from workspaces."""
        paths = []
        for ws in self._workspaces:
            subagent_dir = os.path.join(ws, ".agents", "subagents")
            if os.path.isdir(subagent_dir):
                paths.append(subagent_dir)
        return paths

    def get_skills_search_paths(self) -> List[str]:
        """Returns the effective list of skills search paths, with builtin fallback, absolute and normalized."""
        paths = []
        if self._skills_paths:
            raw_paths = list(self._skills_paths)
        else:
            raw_paths = []
            for ws in self._workspaces:
                ws_skills = os.path.join(ws, "skills")
                ws_agents_skills = os.path.join(ws, ".agents", "skills")
                if os.path.isdir(ws_skills):
                    raw_paths.append(ws_skills)
                if os.path.isdir(ws_agents_skills):
                    raw_paths.append(ws_agents_skills)

        # Always include the script's physical installation directory's builtin/skills folder
        from .utils import get_base_path
        cli_skills_dir = os.path.join(get_base_path(), "builtin", "skills")
        if os.path.isdir(cli_skills_dir) and cli_skills_dir not in raw_paths:
            raw_paths.append(cli_skills_dir)

        # Normalize and deduplicate
        for p in raw_paths:
            if p:
                abs_p = os.path.abspath(os.path.normpath(p))
                if abs_p not in paths:
                    paths.append(abs_p)
        return paths

    def discover_subagents(self, force_refresh: bool = False) -> List[SubagentConfig]:
        """Discovers and returns all subagent configurations from workspace directories.

        Results are cached; use force_refresh=True to invalidate the cache.
        """
        if self._subagent_cache is not None and not force_refresh:
            return self._subagent_cache

        from .subagents import discover_subagents_in_paths
        self._subagent_cache = discover_subagents_in_paths(self.get_subagent_search_paths())
        return self._subagent_cache

    def discover_skills(self, force_refresh: bool = False) -> List[str]:
        """Discovers and returns all skill names from the resolved skills paths.

        Results are cached; use force_refresh=True to invalidate the cache.
        """
        if self._skills_cache is not None and not force_refresh:
            return self._skills_cache

        from .list_skills import discover_skills_in_paths
        self._skills_cache = discover_skills_in_paths(self.get_skills_search_paths())
        return self._skills_cache

    def get_commands_map(self) -> Dict[str, Any]:
        """Discovers, caches, and returns the command map for the REPL."""
        if self._commands_cache is None:
            from .builtin.commands import get_command_map
            self._commands_cache = get_command_map(self._workspaces)
        return self._commands_cache

    def invalidate_cache(self) -> None:
        """Invalidates all cached discovery results."""
        self._subagent_cache = None
        self._skills_cache = None
        self._commands_cache = None
