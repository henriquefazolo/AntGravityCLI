import click
from colorama import Fore, Style
from google.antigravity import Agent

from config import setup_agent_config
from repl import run_repl, stream_chat_response
from parser import preprocess_prompt
from console_io import ConsoleOutputWriter, ConsoleInputReader

async def run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=False, verbose=False):
    """Inicializa as configurações do agente e inicia a execução única ou REPL."""
    try:
        config = setup_agent_config(model, yolo, workspace, system_instruction, api_key, skills_path)
    except (ValueError, IOError) as e:
        click.echo(f"{Fore.RED}{e}{Style.RESET_ALL}", err=True)
        return

    writer = ConsoleOutputWriter()
    reader = ConsoleInputReader()

    if prompt:
        # Prompt Único
        async with Agent(config) as agent:
            processed_prompt = preprocess_prompt(prompt, config.skills_paths)
            await stream_chat_response(agent, processed_prompt, writer, silent=silent, verbose=verbose)
    else:
        # Modo Interativo (REPL)
        async with Agent(config) as agent:
            await run_repl(agent, config.skills_paths, reader, writer, silent=silent, verbose=verbose)
