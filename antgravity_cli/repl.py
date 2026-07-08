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
    
    suggestions = ["/exit", "/quit", "/reset"]
    
    # Resolve script's installation folder directory to load internal CLI skills
    from .utils import get_base_path
    base_dir = get_base_path()
    cli_skills_dir = os.path.join(base_dir, "builtin_agents", "skills")
    
    paths_to_search = list(skills_paths) if skills_paths else []
    if not paths_to_search:
        paths_to_search = ["skills", ".agents/skills", cli_skills_dir]
        
    discovered = discover_skills_in_paths(paths_to_search)
    for s in discovered:
        suggestions.append(f"/{s}")
        
    return sorted(list(set(suggestions)))

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
            user_input = await reader.read_input(
                i18n.t("repl", "prompt_you"),
                suggestions=suggestions,
                file_suggestions=file_suggestions
            )
        except (KeyboardInterrupt, EOFError):
            click.echo(f"\n{Fore.YELLOW}{i18n.t('repl', 'exiting')}{Style.RESET_ALL}")
            break

        if not user_input:
            continue

        if user_input in ("/exit", "/quit"):
            click.echo(f"{Fore.YELLOW}{i18n.t('repl', 'exiting')}{Style.RESET_ALL}")
            break

        if user_input == "/reset":
            agent.conversation.clear_history()
            click.echo(i18n.t("repl", "conversation_history_cleared"))
            continue

        processed_input = preprocess_prompt(user_input, resolved_skills)
        await stream_chat_response(agent, processed_input, writer, silent=silent, verbose=verbose)
