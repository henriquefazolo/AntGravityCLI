import click
from colorama import Fore, Style
from google.antigravity import Agent

import i18n
from config import setup_agent_config
from repl import run_repl, stream_chat_response
from parser import preprocess_prompt
from console_io import ConsoleOutputWriter, ConsoleInputReader

async def run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=False, verbose=False, language="en-us"):
    """Initializes the agent configurations and starts either a single execution or the REPL."""
    i18n.set_language(language)
    try:
        config = setup_agent_config(model, yolo, workspace, system_instruction, api_key, skills_path)
    except (ValueError, IOError) as e:
        click.echo(f"{Fore.RED}{e}{Style.RESET_ALL}", err=True)
        return

    writer = ConsoleOutputWriter()
    reader = ConsoleInputReader()

    if prompt:
        # Single Prompt
        async with Agent(config) as agent:
            processed_prompt = preprocess_prompt(prompt, config.skills_paths)
            await stream_chat_response(agent, processed_prompt, writer, silent=silent, verbose=verbose)
    else:
        # Interactive Mode (REPL)
        async with Agent(config) as agent:
            await run_repl(agent, config.skills_paths, reader, writer, silent=silent, verbose=verbose)
