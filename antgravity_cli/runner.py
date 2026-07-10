import sys
import click
from colorama import Fore, Style
from google.antigravity import Agent

from . import i18n
from .config import setup_agent_config
from .repl import run_repl, stream_chat_response
from .parser import preprocess_prompt
from .console_io import ConsoleOutputWriter, ConsoleInputReader

async def run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=False, verbose=False, verbose_subagents=False, language="en-us"):
    """Initializes the agent configurations and starts either a single execution or the REPL."""
    i18n.set_language(language)
    try:
        config = setup_agent_config(model, yolo, workspace, system_instruction, api_key, skills_path)
    except (ValueError, IOError) as e:
        click.echo(f"{Fore.RED}{e}{Style.RESET_ALL}", err=True)
        return

    writer = ConsoleOutputWriter()
    reader = ConsoleInputReader()

    # Detect piped input (stdin redirected)
    piped_prompt = None
    if not prompt and not sys.stdin.isatty():
        try:
            piped_prompt = sys.stdin.read().strip()
        except Exception:
            pass

    effective_prompt = prompt or piped_prompt

    try:
        if effective_prompt:
            # Single Prompt (interactive prompt argument or piped stdin)
            async with Agent(config) as agent:
                processed_prompt = preprocess_prompt(effective_prompt, config.skills_paths)
                await stream_chat_response(agent, processed_prompt, writer, silent=silent, verbose=verbose, verbose_subagents=verbose_subagents)
        else:
            # Interactive Mode (REPL)
            async with Agent(config) as agent:
                await run_repl(agent, config.skills_paths, reader, writer, silent=silent, verbose=verbose, verbose_subagents=verbose_subagents)
    except Exception as e:
        click.echo(f"{Fore.RED}{i18n.t('runner', 'failed_to_run_agent', error=str(e))}{Style.RESET_ALL}", err=True)
