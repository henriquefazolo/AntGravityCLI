import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import asyncio
import os
import click
from colorama import Fore, Style
from google.antigravity.types import Thought, Text, ToolCall, ToolResult
from . import i18n
from .interfaces import OutputWriter, InputReader
from .console_io import ConsoleOutputWriter, ConsoleInputReader
from .parser import preprocess_prompt

def _extract_subagent_name(args) -> str | None:
    """Helper to extract subagent name from start_subagent tool call arguments."""
    if not args:
        return None
    if isinstance(args, dict):
        for key in ("agent_name", "name", "subagent_name"):
            if key in args and args[key]:
                return str(args[key])
    elif isinstance(args, str):
        import json
        try:
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                for key in ("agent_name", "name", "subagent_name"):
                    if key in parsed and parsed[key]:
                        return str(parsed[key])
        except Exception:
            return args.strip()
    return None

def get_subagent_name_by_id(agent, traj_id: str) -> str:
    """Resolves a subagent name from a trajectory ID by inspecting history."""
    if not traj_id:
        return "Subagent"
    try:
        main_id = getattr(agent.conversation.connection, "_main_trajectory_id", None)
        if traj_id == main_id:
            return "Parent"
        
        history = agent.conversation.history
        for step in reversed(history):
            if step.tool_calls:
                for call in step.tool_calls:
                    if call.name == "start_subagent":
                        name = _extract_subagent_name(call.args)
                        if name:
                            return name
    except Exception:
        pass
    return "Subagent"

async def stream_chat_response(agent, prompt, writer: OutputWriter = None, silent=False, verbose=False, verbose_subagents=False):
    """Runs the chat and streams the response (thoughts, tools, and text) in real time."""
    if writer is None:
        writer = ConsoleOutputWriter()
        
    try:
        writer.reset()
        writer.start_loading()
        response = await agent.chat(prompt)
        
        traj_name_cache = {}
        async for chunk in response.chunks:
            is_subagent = False
            subagent_name = "Subagent"
            try:
                history = agent.conversation.history
                
                # Retrieve step index if it exists (Thought, Text chunks)
                chunk_step_idx = getattr(chunk, "step_index", None)
                chunk_name = getattr(chunk, "name", None)
                chunk_id = getattr(chunk, "id", None)
                
                for s in reversed(history):
                    matched = False
                    if chunk_step_idx is not None and s.step_index == chunk_step_idx:
                        matched = True
                    elif chunk_name is not None and s.tool_calls:
                        for tc in s.tool_calls:
                            if tc.name == chunk_name and getattr(tc, "id", None) == chunk_id:
                                matched = True
                                break
                                
                    if matched:
                        main_id = getattr(agent.conversation.connection, "_main_trajectory_id", None)
                        traj_id = getattr(s, "trajectory_id", None)
                        if main_id and traj_id and traj_id != main_id:
                            is_subagent = True
                            if traj_id in traj_name_cache:
                                subagent_name = traj_name_cache[traj_id]
                            else:
                                subagent_name = get_subagent_name_by_id(agent, traj_id)
                                traj_name_cache[traj_id] = subagent_name
                        break
            except Exception:
                pass

            if isinstance(chunk, Thought):
                if is_subagent:
                    if verbose_subagents and not silent:
                        writer.write_thought(f"[{subagent_name}] {chunk.text}")
                else:
                    if verbose and not silent:
                        writer.write_thought(chunk.text)
            elif isinstance(chunk, Text):
                writer.write_text(chunk.text)
            elif isinstance(chunk, ToolCall):
                if is_subagent:
                    if verbose_subagents and not silent:
                        writer.write_tool_call(f"[{subagent_name}] {chunk.name}", chunk.args)
                else:
                    if not silent:
                        writer.write_tool_call(chunk.name, chunk.args)
            elif isinstance(chunk, ToolResult):
                if is_subagent:
                    if verbose_subagents and not silent:
                        writer.write_tool_result(f"[{subagent_name}] {chunk.name}", chunk.result, chunk.error)
                else:
                    if not silent:
                        writer.write_tool_result(chunk.name, chunk.result, chunk.error)
        
        writer.stop_loading()
        writer.reset()
        print() # Final line break for alignment
    except Exception as e:
        writer.stop_loading()
        click.echo(i18n.t("repl", "error_during_conversation", error=str(e)), err=True)

def _get_repl_suggestions(skills_paths_or_context, force_refresh: bool = True) -> list[str]:
    """Scans registered skills folders and returns formatted skill commands and triggers."""
    from .builtin.commands import get_command_triggers
    from .workspace_context import WorkspaceContext
    
    ws_workspaces = None
    if isinstance(skills_paths_or_context, WorkspaceContext):
        ws_workspaces = skills_paths_or_context.workspaces
        discovered = skills_paths_or_context.discover_skills(force_refresh=force_refresh)
    else:
        ws_context = WorkspaceContext(workspaces=None, skills_paths=skills_paths_or_context)
        ws_workspaces = ws_context.workspaces
        discovered = ws_context.discover_skills(force_refresh=force_refresh)
        
    suggestions = get_command_triggers(ws_workspaces)
    for s in discovered:
        if s != "skill_example":
            suggestions.append(f"/{s}")
        
    return sorted(list(set(suggestions)))

def get_active_subagent_name(agent) -> str | None:
    """Helper to extract the last active subagent name from conversation history."""
    try:
        history = agent.conversation.history
        for step in reversed(history):
            if step.tool_calls:
                for call in step.tool_calls:
                    if call.name == "start_subagent":
                        name = _extract_subagent_name(call.args)
                        if name:
                            return name
    except Exception:
        pass
    return None

async def run_repl(agent, resolved_skills, reader: InputReader = None, writer: OutputWriter = None, silent=False, verbose=False, verbose_subagents=False):
    """Runs the interactive terminal (REPL) conversing with the agent."""
    if reader is None:
        reader = ConsoleInputReader()
    if writer is None:
        writer = ConsoleOutputWriter()
        
    if not hasattr(agent, "_disabled_skills"):
        agent._disabled_skills = set()
    if not hasattr(agent, "_disabled_subagents"):
        agent._disabled_subagents = set()

    from .workspace_context import WorkspaceContext
    config = getattr(agent, "_config", None) or getattr(agent, "config", None)
    ws_context = getattr(config, "_ws_context", None)
    if ws_context is None:
        workspaces = getattr(config, "workspaces", None) or [os.path.abspath(".")]
        ws_context = WorkspaceContext(workspaces, resolved_skills)

    suggestions = _get_repl_suggestions(ws_context)
    
    from .utils import get_workspace_files_and_folders
    file_suggestions = []
    workspaces = getattr(config, "workspaces", None) or [os.path.abspath(".")]
    for ws in workspaces:
        file_suggestions.extend(get_workspace_files_and_folders(ws))
    file_suggestions = sorted(list(set(file_suggestions)))
    
    from . import __version__
    app_version = __version__

    # Render Option 1 colorized solid block ant art logo
    click.echo(f"\n{i18n.t('repl', 'version_label', version=app_version)}")
    click.echo("")
    click.echo(f"  {Fore.CYAN}▄▀▀▄       ▄▀▀▄{Style.RESET_ALL}")
    click.echo(f"   {Fore.CYAN}▀▄ ▀▄   ▄▀ ▄▀{Style.RESET_ALL}")
    click.echo(f"    {Fore.BLUE}▄█████████▄{Style.RESET_ALL}")
    click.echo(f"   {Fore.BLUE}██{Fore.GREEN}███{Fore.BLUE}███{Fore.GREEN}███{Fore.BLUE}██{Style.RESET_ALL}")
    click.echo(f"   {Fore.BLUE}█████████████{Style.RESET_ALL}")
    click.echo(f"    {Fore.BLUE}▀█████████▀{Style.RESET_ALL}")
    click.echo(f"      {Fore.CYAN}▄█▀ ▀█▄{Style.RESET_ALL}")
        
    click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}{i18n.t('repl', 'repl_title')}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{i18n.t('repl', 'special_commands_label')}{Style.RESET_ALL}")
    click.echo(f"  {Fore.GREEN}/exit{Style.RESET_ALL} or {Fore.GREEN}/quit{Style.RESET_ALL} - {i18n.t('repl', 'command_exit_desc')}")
    click.echo(f"  {Fore.GREEN}/reset{Style.RESET_ALL}         - {i18n.t('repl', 'command_reset_desc')}")
    
    # Display active skills with compact banner format if there are more than 5
    skills = [s.lstrip("/") for s in suggestions if s not in ("/exit", "/quit", "/reset")]
    if skills:
        if len(skills) > 5:
            click.echo(i18n.t('repl', 'active_skills_banner', count=len(skills)))
        else:
            formatted_skills = [f"  {Fore.GREEN}/{s}{Style.RESET_ALL}" for s in skills]
            for fs in formatted_skills:
                click.echo(fs)
                
    click.echo("-" * 40)
    
    import time
    last_cache_time = 0.0
    cache_ttl = 5.0
    cached_suggestions = []
    cached_file_suggestions = []
    cached_active_subagents = []
    
    while True:
        try:
            current_time = time.time()
            cache_invalidated = (ws_context._subagent_cache is None or ws_context._skills_cache is None)
            
            if cache_invalidated or (current_time - last_cache_time > cache_ttl):
                do_force = cache_invalidated or (current_time - last_cache_time > cache_ttl)
                cached_suggestions = _get_repl_suggestions(ws_context, force_refresh=do_force)
                
                file_suggestions = []
                for ws in workspaces:
                    file_suggestions.extend(get_workspace_files_and_folders(ws))
                cached_file_suggestions = sorted(list(set(file_suggestions)))
                
                cached_active_subagents = ws_context.discover_subagents(force_refresh=do_force)
                last_cache_time = current_time
            
            # Filter out disabled skills dynamically
            disabled_skills = getattr(agent, "_disabled_skills", set())
            suggestions = [s for s in cached_suggestions if s.lstrip("/") not in disabled_skills]
            file_suggestions = cached_file_suggestions
            
            # Filter out disabled subagents and example templates dynamically
            disabled_agents = getattr(agent, "_disabled_subagents", set())
            active_subagents = [sa for sa in cached_active_subagents if sa.name not in disabled_agents and sa.name != "subagent_example"]
            subagent_names = [sa.name for sa in active_subagents]
            
            # Sync in-memory agent configuration subagents list
            if config:
                config.subagents = active_subagents

            base_prompt = i18n.t("repl", "prompt_you")
            active_subagent = get_active_subagent_name(agent)
            if active_subagent:
                if " >" in base_prompt:
                    prompt_text = base_prompt.replace(" >", f" (-> {active_subagent}) >")
                else:
                    prompt_text = f"{base_prompt.strip()} (-> {active_subagent}) > "
            else:
                prompt_text = base_prompt

            user_input = await reader.read_input(
                prompt_text,
                suggestions=suggestions,
                file_suggestions=file_suggestions,
                subagent_suggestions=subagent_names
            )
        except (KeyboardInterrupt, EOFError):
            click.echo(f"\n{Fore.YELLOW}{i18n.t('repl', 'exiting')}{Style.RESET_ALL}")
            break

        if not user_input:
            continue

        parts = user_input.strip().split(maxsplit=1)
        cmd_trigger = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""

        from .builtin.commands import get_command_map
        commands_map = get_command_map(workspaces)
        if cmd_trigger in commands_map:
            continue_repl = await commands_map[cmd_trigger].execute(agent, context=cmd_args)
            if not continue_repl:
                break
            continue

        processed_input = preprocess_prompt(user_input, resolved_skills, disabled_skills=disabled_skills)
        await stream_chat_response(agent, processed_input, writer, silent=silent, verbose=verbose, verbose_subagents=verbose_subagents)
