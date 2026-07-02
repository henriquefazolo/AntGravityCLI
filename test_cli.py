import unittest
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
import os
from colorama import Fore, Style

# Import the CLI and functions to test
from main import main
from runner import run_cli
from config import setup_agent_config
from parser import preprocess_prompt
from handlers import cli_ask_user_handler
from console_io import ConsoleOutputWriter

class TestAntigravityCLIFunctionality(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_help_flag(self):
        """Verifica se o comando help/ajuda é exibido corretamente."""
        result = self.runner.invoke(main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Usage:', result.output)
        self.assertIn('--model', result.output)
        self.assertIn('--yolo', result.output)
        self.assertIn('--workspace', result.output)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Verifica se o erro correto é exibido quando a API Key está ausente."""
        result = self.runner.invoke(main, ['--api-key', '', 'Olá'])
        self.assertIn('Erro: A chave de API do Gemini não foi encontrada', result.output)

    @patch('builtins.input', return_value='y')
    def test_cli_ask_user_handler_approve(self, mock_input):
        """Verifica se o gerenciador de políticas aceita 'y' de confirmação do usuário."""
        mock_tool_call = MagicMock()
        mock_tool_call.name = "RUN_COMMAND"
        mock_tool_call.args = {"cmd": "dir"}
        
        approved = cli_ask_user_handler(mock_tool_call)
        self.assertTrue(approved)

    @patch('builtins.input', return_value='n')
    def test_cli_ask_user_handler_reject(self, mock_input):
        """Verifica se o gerenciador de políticas rejeita 'n' de confirmação do usuário."""
        mock_tool_call = MagicMock()
        mock_tool_call.name = "RUN_COMMAND"
        mock_tool_call.args = {"cmd": "rm -rf /"}
        
        approved = cli_ask_user_handler(mock_tool_call)
        self.assertFalse(approved)

    @patch('runner.Agent')
    @patch('config.LocalAgentConfig')
    @patch('runner.stream_chat_response')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake_test_key'})
    def test_cli_runs_with_prompt(self, mock_stream, mock_config, mock_agent):
        """Verifica se o fluxo básico de chamada com prompt funciona e invoca os agentes corretos."""
        # Criando mocks para o gerenciador de contexto do Agent
        mock_agent_instance = MagicMock()
        mock_agent.return_value.__aenter__.return_value = mock_agent_instance
        
        result = self.runner.invoke(main, ['Oi'])
        self.assertEqual(result.exit_code, 0)
        
        # Garante que o Agent e a config foram instanciados corretamente
        mock_config.assert_called_once()
        mock_agent.assert_called_once_with(mock_config.return_value)
        
        # Garante que o stream_chat_response foi chamado com os parâmetros corretos, incluindo o writer
        args, kwargs = mock_stream.call_args
        self.assertEqual(args[0], mock_agent_instance)
        self.assertEqual(args[1], 'Oi')
        self.assertIsInstance(args[2], ConsoleOutputWriter)
        self.assertEqual(kwargs.get('silent'), False)

    @patch('runner.Agent')
    @patch('config.LocalAgentConfig')
    @patch('runner.stream_chat_response')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake_test_key'})
    def test_cli_runs_with_silent_flag(self, mock_stream, mock_config, mock_agent):
        """Verifica se a flag --silent é propagada corretamente para o stream."""
        mock_agent_instance = MagicMock()
        mock_agent.return_value.__aenter__.return_value = mock_agent_instance
        
        result = self.runner.invoke(main, ['--silent', 'Oi'])
        self.assertEqual(result.exit_code, 0)
        
        # Garante que o stream_chat_response foi chamado com silent=True e o writer injetado
        args, kwargs = mock_stream.call_args
        self.assertEqual(args[0], mock_agent_instance)
        self.assertEqual(args[1], 'Oi')
        self.assertIsInstance(args[2], ConsoleOutputWriter)
        self.assertEqual(kwargs.get('silent'), True)

    def test_preprocess_prompt_file_injection(self):
        """Verifica se referências a @arquivo são injetadas com o conteúdo do arquivo."""
        # Criar arquivo temporário para teste
        temp_file = "temp_test_file.txt"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("Conteudo de teste do arquivo temporario.")
            
            prompt = f"Analise o arquivo @{temp_file} por favor."
            processed = preprocess_prompt(prompt)
            
            self.assertIn("=== CONTEÚDO DO ARQUIVO: temp_test_file.txt", processed)
            self.assertIn("Conteudo de teste do arquivo temporario.", processed)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_preprocess_prompt_skill_injection(self):
        """Verifica se referências a /skill são injetadas com as regras do SKILL.md."""
        # Criar skill temporária
        temp_skills_dir = "temp_skills"
        temp_skill_name = "test_skill"
        skill_dir = os.path.join(temp_skills_dir, temp_skill_name)
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        
        try:
            os.makedirs(skill_dir, exist_ok=True)
            with open(skill_md_path, "w", encoding="utf-8") as f:
                f.write("---\nname: Test Skill\ndescription: Test description\n---\nRegras da skill de teste.")
                
            prompt = f"Use a skill /{temp_skill_name} para rodar."
            processed = preprocess_prompt(prompt, skills_paths=[temp_skills_dir])
            
            self.assertIn("=== INSTRUÇÕES DA SKILL: test_skill", processed)
            self.assertIn("Regras da skill de teste.", processed)
        finally:
            # Limpar pastas e arquivos criados
            if os.path.exists(skill_md_path):
                os.remove(skill_md_path)
            if os.path.exists(skill_dir):
                os.rmdir(skill_dir)
            if os.path.exists(temp_skills_dir):
                os.rmdir(temp_skills_dir)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake_key'})
    def test_setup_agent_config_success(self):
        """Verifica se a configuração do agente é gerada com sucesso."""
        config = setup_agent_config(
            model='gemini-3.5-flash',
            yolo=False,
            workspace=[],
            system_instruction=None,
            api_key=None,
            skills_path=[]
        )
        self.assertEqual(config.model, 'gemini-3.5-flash')
        self.assertEqual(config.api_key, 'fake_key')
        self.assertFalse(config.skills_paths)

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_agent_config_missing_key(self):
        """Verifica se ValueError é lançado quando a API Key está ausente."""
        with self.assertRaises(ValueError):
            setup_agent_config(
                model='gemini-3.5-flash',
                yolo=False,
                workspace=[],
                system_instruction=None,
                api_key=None,
                skills_path=[]
            )

    def test_prompt_preprocessor_ocp_extensibility(self):
        """Verifica se novos processadores de diretivas podem ser adicionados sem alterar o código existente (OCP)."""
        import re
        from interfaces import DirectiveProcessor
        from parser import PromptPreprocessor
        
        class MockIssueDirectiveProcessor(DirectiveProcessor):
            def process(self, prompt: str, skills_paths=None):
                match = re.search(r'#issue-(\d+)', prompt)
                extra = []
                if match:
                    issue_id = match.group(1)
                    extra.append(f"=== DETALHES DA ISSUE #{issue_id} ===\nCorrigir bug de login no sistema.")
                return prompt, extra

        preprocessor = PromptPreprocessor(processors=[MockIssueDirectiveProcessor()])
        
        prompt = "Resolva a issue #issue-999"
        processed = preprocessor.preprocess(prompt)
        
        self.assertIn("=== DETALHES DA ISSUE #999 ===", processed)
        self.assertIn("Corrigir bug de login no sistema.", processed)

    @patch('repl.click.echo')
    def test_run_repl_exit_command(self, mock_echo):
        """Verifica se o REPL encerra e imprime 'Saindo...' ao receber /quit."""
        import asyncio
        from repl import run_repl
        from interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None) -> str:
                return "/quit"
                
        mock_agent = MagicMock()
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        mock_echo.assert_called_with(f"{Fore.YELLOW}Saindo...{Style.RESET_ALL}")

if __name__ == '__main__':
    unittest.main()
