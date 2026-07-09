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

async def stream_chat_response(agent, prompt, writer: OutputWriter = None, silent=False, verbose=False):
    """Runs the chat and streams the response (thoughts, tools, and text) in real time."""
    if writer is None:
        writer = ConsoleOutputWriter()
        
    try:
        writer.reset()
        writer.start_loading()
        response = await agent.chat(prompt)
        
        async for chunk in response.chunks:
            if isinstance(chunk, Thought):
                if verbose and not silent:
                    writer.write_thought(chunk.text)
            elif isinstance(chunk, Text):
                writer.write_text(chunk.text)
            elif isinstance(chunk, ToolCall):
                if not silent:
                    writer.write_tool_call(chunk.name, chunk.args)
            elif isinstance(chunk, ToolResult):
                if not silent:
                    writer.write_tool_result(chunk.name, chunk.result, chunk.error)
        
        writer.stop_loading()
        writer.reset()
        print() # Final line break for alignment
    except Exception as e:
        writer.stop_loading()
        click.echo(i18n.t("repl", "error_during_conversation", error=str(e)), err=True)

def _get_repl_suggestions(skills_paths: list[str]) -> list[str]:
    """Scans registered skills folders and returns formatted skill commands and triggers."""
    from .list_skills import discover_skills_in_paths
    from .builtin.commands import get_command_triggers
    suggestions = get_command_triggers()
    
    # Resolve script's installation folder directory to load internal CLI skills
    from .utils import get_base_path
    base_dir = get_base_path()
    cli_skills_dir = os.path.join(base_dir, "builtin", "skills")
    
    paths_to_search = list(skills_paths) if skills_paths else []
    if not paths_to_search:
        paths_to_search = ["skills", ".agents/skills", cli_skills_dir]
        
    discovered = discover_skills_in_paths(paths_to_search)
    for s in discovered:
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
                        args = call.args
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
    except Exception:
        pass
    return None

async def run_repl(agent, resolved_skills, reader: InputReader = None, writer: OutputWriter = None, silent=False, verbose=False):
    """Runs the interactive terminal (REPL) conversing with the agent."""
    if reader is None:
        reader = ConsoleInputReader()
    if writer is None:
        writer = ConsoleOutputWriter()
        
    suggestions = _get_repl_suggestions(resolved_skills)
    
    from .utils import get_workspace_files_and_folders
    file_suggestions = []
    config = getattr(agent, "_config", None) or getattr(agent, "config", None)
    workspaces = getattr(config, "workspaces", None) or [os.path.abspath(".")]
    for ws in workspaces:
        file_suggestions.extend(get_workspace_files_and_folders(ws))
    file_suggestions = sorted(list(set(file_suggestions)))
    
    # Render Option 1 colorized solid block ant art logo
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
    
    # Display active skills limited to 5 with an "and more" suffix
    skills = [s.lstrip("/") for s in suggestions if s not in ("/exit", "/quit", "/reset")]
    if skills:
        formatted_skills = [f"  {Fore.GREEN}/{s}{Style.RESET_ALL}" for s in skills]
        if len(formatted_skills) > 5:
            for fs in formatted_skills[:5]:
                click.echo(fs)
            click.echo(f"  ... {i18n.t('repl', 'and_more')}")
        else:
            for fs in formatted_skills:
                click.echo(fs)

    click.echo(f"{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")

    while True:
        try:
            # Recalculate suggestions dynamically on each prompt iteration so newly created files and skills are suggested immediately
            suggestions = _get_repl_suggestions(resolved_skills)
            
            file_suggestions = []
            for ws in workspaces:
                file_suggestions.extend(get_workspace_files_and_folders(ws))
            file_suggestions = sorted(list(set(file_suggestions)))

            # Discover subagents dynamically to allow autocompleting newly added subagents
            subagent_paths = []
            for ws in workspaces:
                workspace_subagents = os.path.join(ws, ".agents", "subagents")
                if os.path.isdir(workspace_subagents):
                    subagent_paths.append(workspace_subagents)
            
            from .subagents import discover_subagents_in_paths
            discovered_subagents = discover_subagents_in_paths(subagent_paths)
            subagent_names = [sa.name for sa in discovered_subagents]
            
            # Sync in-memory agent configuration subagents list
            if config:
                config.subagents = discovered_subagents

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

        from .builtin.commands import get_command_map
        commands_map = get_command_map()
        if user_input in commands_map:
            continue_repl = await commands_map[user_input].execute(agent)
            if not continue_repl:
                break
            continue

        processed_input = preprocess_prompt(user_input, resolved_skills)
        await stream_chat_response(agent, processed_input, writer, silent=silent, verbose=verbose)
