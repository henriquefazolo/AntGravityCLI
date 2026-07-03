import asyncio
import os
import click
from dotenv import load_dotenv
from utils import get_base_path

# Load API keys and configurations from .env files
# 1. Load configuration from the script's installation directory .env (global defaults)
base_env = os.path.join(get_base_path(), ".env")
if os.path.exists(base_env):
    load_dotenv(base_env)

# 2. Load configuration from the current working directory (CWD) .env (workspace-specific override)
cwd_env = os.path.abspath(".env")
if os.path.exists(cwd_env) and os.path.normcase(cwd_env) != os.path.normcase(os.path.abspath(base_env)):
    load_dotenv(cwd_env, override=True)

from runner import run_cli

@click.command()
@click.argument('prompt', required=False)
@click.option('--model', '-m', envvar='GEMINI_MODEL', default='gemini-3.1-flash-lite', help='Gemini model to be used.')
@click.option('--yolo', '-y', is_flag=True, envvar='ANTGRAVITY_YOLO', help='Bypass safety confirmations and execute all actions automatically.')
@click.option('--workspace', '-w', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Restrict file tools to these directories (default: current directory).')
@click.option('--system-instruction', '-s', help='System instructions text or path to a file with instructions.')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API key.')
@click.option('--skills-path', '-k', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Path to skills folders (can be repeated).')
@click.option('--silent', is_flag=True, help='Hide thoughts and tool executions in the terminal.')
@click.option('--verbose', '-v', is_flag=True, help='Display the agent\'s internal reasoning thoughts in the console.')
@click.option('--language', '-l', envvar='ANTGRAVITY_LANG', default='en-us', help='Output language (e.g. en-us, pt-br).')
def main(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent, verbose, language):
    """AntGravity CLI - Terminal-based interface for Google Antigravity agents."""
    asyncio.run(run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=silent, verbose=verbose, language=language))

if __name__ == "__main__":
    main()

