import asyncio
import click
from dotenv import load_dotenv

# Carrega chaves de API e configurações de um arquivo .env se presente
load_dotenv()

from runner import run_cli

@click.command()
@click.argument('prompt', required=False)
@click.option('--model', '-m', default='gemini-3.1-flash-lite', help='Modelo do Gemini a ser utilizado.')
@click.option('--yolo', '-y', is_flag=True, help='Ignorar confirmações de segurança e executar todas as ações automaticamente.')
@click.option('--workspace', '-w', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Restringir ferramentas de arquivos a estes diretórios (padrão: diretório atual).')
@click.option('--system-instruction', '-s', help='Texto de instruções do sistema ou caminho para arquivo com instruções.')
@click.option('--api-key', help='Chave de API do Gemini.')
@click.option('--skills-path', '-k', multiple=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Caminho para pastas de skills (pode ser repetido).')
@click.option('--silent', is_flag=True, help='Ocultar pensamentos e execuções de ferramentas no terminal.')
@click.option('--verbose', '-v', is_flag=True, help='Exibir pensamentos internos de raciocínio do agente no console.')
def main(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent, verbose):
    """Antigravity CLI - Terminal-based interface for Google Antigravity agents."""
    asyncio.run(run_cli(prompt, model, yolo, workspace, system_instruction, api_key, skills_path, silent=silent, verbose=verbose))

if __name__ == "__main__":
    main()
