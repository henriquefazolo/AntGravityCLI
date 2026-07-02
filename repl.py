import asyncio
import os
import click
from colorama import Fore, Style
from google.antigravity.types import Thought, Text, ToolCall, ToolResult
from interfaces import OutputWriter, InputReader
from console_io import ConsoleOutputWriter, ConsoleInputReader
from parser import preprocess_prompt

async def stream_chat_response(agent, prompt, writer: OutputWriter = None, silent=False, verbose=False):
    """Executa o chat e transmite a resposta (pensamentos, ferramentas e texto) em tempo real."""
    if writer is None:
        writer = ConsoleOutputWriter()
        
    try:
        writer.reset()
        writer.start_loading("Pensando...")
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
        print() # Quebra de linha final para alinhamento
    except Exception as e:
        writer.stop_loading()
        click.echo(f"Erro durante a conversação: {e}", err=True)

def _get_repl_suggestions(skills_paths: list[str]) -> list[str]:
    """Varre as pastas de skills registradas e retorna comandos e gatilhos de skills formatados."""
    suggestions = ["/exit", "/quit", "/reset"]
    for path in skills_paths:
        if path and os.path.exists(path) and os.path.isdir(path):
            try:
                for entry in os.listdir(path):
                    entry_path = os.path.join(path, entry)
                    if os.path.isdir(entry_path):
                        # Se contiver o arquivo SKILL.md, é uma skill ativa
                        if os.path.exists(os.path.join(entry_path, "SKILL.md")):
                            suggestions.append(f"/{entry}")
            except Exception:
                pass
    return sorted(list(set(suggestions)))

async def run_repl(agent, resolved_skills, reader: InputReader = None, writer: OutputWriter = None, silent=False, verbose=False):
    """Executa o terminal interativo (REPL) conversando com o agente."""
    if reader is None:
        reader = ConsoleInputReader()
    if writer is None:
        writer = ConsoleOutputWriter()
        
    suggestions = _get_repl_suggestions(resolved_skills)
        
    click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== Antigravity CLI (Modo Interativo) ==={Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}Digite suas mensagens. Comandos especiais:{Style.RESET_ALL}")
    click.echo(f"  {Fore.GREEN}/exit{Style.RESET_ALL} ou {Fore.GREEN}/quit{Style.RESET_ALL} - Sair do CLI")
    click.echo(f"  {Fore.GREEN}/reset{Style.RESET_ALL}         - Reiniciar o histórico da conversa")
    click.echo(f"{Fore.MAGENTA}{'-' * 40}{Style.RESET_ALL}")

    while True:
        try:
            user_input = await reader.read_input("Você > ", suggestions=suggestions)
        except (KeyboardInterrupt, EOFError):
            click.echo(f"\n{Fore.YELLOW}Saindo...{Style.RESET_ALL}")
            break

        if not user_input:
            continue

        if user_input in ("/exit", "/quit"):
            click.echo(f"{Fore.YELLOW}Saindo...{Style.RESET_ALL}")
            break

        if user_input == "/reset":
            agent.conversation.clear_history()
            click.echo("Histórico da conversa limpo!")
            continue

        processed_input = preprocess_prompt(user_input, resolved_skills)
        await stream_chat_response(agent, processed_input, writer, silent=silent, verbose=verbose)
