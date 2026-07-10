import asyncio
import os
import sys
import click
from dotenv import load_dotenv
from .utils import get_base_path

# Load API keys and configurations from .env files
# Check if a custom env file was specified via CLI arguments before processing options
custom_env_path = None
for i, arg in enumerate(sys.argv):
    if arg in ("--env-file", "-e") and i + 1 < len(sys.argv):
        custom_env_path = sys.argv[i + 1]
        break

if custom_env_path:
    # If a custom .env path is provided, we load only it and let it override existing variables
    if os.path.exists(custom_env_path):
        load_dotenv(custom_env_path, override=True)
else:
    # 1. Load configuration from the script's installation directory .env (global defaults)
    base_env = os.path.join(get_base_path(), ".env")
    if os.path.exists(base_env):
        load_dotenv(base_env)

    # 2. Load configuration from the current working directory (CWD) .env (workspace-specific override)
    cwd_env = os.path.abspath(".env")
    if os.path.exists(cwd_env) and os.path.normcase(cwd_env) != os.path.normcase(os.path.abspath(base_env)):
        load_dotenv(cwd_env, override=True)

import colorama
from importlib.metadata import version, PackageNotFoundError

# Centralized colorama initialization for console colors
colorama.init()

try:
    __version__ = version("AntGravityCLI")
except PackageNotFoundError:
    __version__ = "1.2.0"

from .runner import run_cli


@click.group(invoke_without_command=True)
@click.version_option(__version__, '--version', '-V', message='%(prog)s %(version)s')
@click.argument('prompt', required=False)
@click.option('--model', '-m', envvar='GEMINI_MODEL', default='gemini-3.1-flash-lite', help='Gemini model to be used.')
@click.option('--yolo', '-y', is_flag=True, envvar='ANTGRAVITY_YOLO', help='Bypass safety confirmations and execute all actions automatically.')
@click.option('--workspace', '-w', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), envvar='ANTGRAVITY_WORKSPACE', help='Restrict file tools to these directories (default: current directory).')
@click.option('--system-instruction', '-s', envvar='ANTGRAVITY_SYSTEM_INSTRUCTION', help='System instructions text or path to a file with instructions.')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API key.')
@click.option('--skills-path', '-k', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), envvar='ANTGRAVITY_SKILLS_PATH', help='Path to skills folders (can be repeated).')
@click.option('--silent', is_flag=True, envvar='ANTGRAVITY_SILENT', help='Hide thoughts and tool executions in the terminal.')
@click.option('--verbose', '-v', is_flag=True, envvar='ANTGRAVITY_VERBOSE', help='Display the agent\'s internal reasoning thoughts in the console.')
@click.option('--verbose-subagents', is_flag=True, envvar='ANTGRAVITY_VERBOSE_SUBAGENTS', help='Display internal reasoning thoughts and tool execution logs for subagents.')
@click.option('--language', '-l', envvar='ANTGRAVITY_LANG', default='en-us', help='Output language (e.g. en-us, pt-br).')
@click.option('--env-file', '-e', type=click.Path(exists=True, file_okay=True, dir_okay=False), help='Path to a custom .env file to load configurations from.')
@click.pass_context
def main(ctx, prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent, verbose, verbose_subagents, language, env_file):
    """AntGravity CLI - Terminal-based interface for Google Antigravity agents."""
    if ctx.invoked_subcommand is not None:
        return

    asyncio.run(run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=silent, verbose=verbose, verbose_subagents=verbose_subagents, language=language))


@main.command()
@click.option('--language', '-l', envvar='ANTGRAVITY_LANG', default='en-us', help='Output language for the wizard (e.g. en-us, pt-br).')
def init(language):
    """Initialize a new AntGravity workspace with customization folders and .env configuration."""
    from . import i18n
    i18n.set_language(language)
    from .init_project import run_init
    run_init()


if __name__ == "__main__":
    main()
