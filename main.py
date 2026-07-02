import asyncio
import click
from dotenv import load_dotenv

# Load API keys and configurations from a .env file if present
load_dotenv()

from runner import run_cli

@click.command()
@click.argument('prompt', required=False)
@click.option('--model', '-m', default='gemini-3.1-flash-lite', help='Gemini model to be used.')
@click.option('--yolo', '-y', is_flag=True, help='Bypass safety confirmations and execute all actions automatically.')
@click.option('--workspace', '-w', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Restrict file tools to these directories (default: current directory).')
@click.option('--system-instruction', '-s', help='System instructions text or path to a file with instructions.')
@click.option('--api-key', help='Gemini API key.')
@click.option('--skills-path', '-k', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Path to skills folders (can be repeated).')
@click.option('--silent', is_flag=True, help='Hide thoughts and tool executions in the terminal.')
@click.option('--verbose', '-v', is_flag=True, help='Display the agent\'s internal reasoning thoughts in the console.')
@click.option('--language', '-l', default='en-us', help='Output language (e.g. en-us, pt-br).')
def main(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent, verbose, language):
    """AntGravity CLI - Terminal-based interface for Google Antigravity agents."""
    asyncio.run(run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=silent, verbose=verbose, language=language))

if __name__ == "__main__":
    main()
