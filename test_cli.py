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
import i18n

class TestAntigravityCLIFunctionality(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        i18n.set_language("en-us")

    def test_help_flag(self):
        """Verify that the help command is displayed correctly."""
        result = self.runner.invoke(main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Usage:', result.output)
        self.assertIn('--model', result.output)
        self.assertIn('--yolo', result.output)
        self.assertIn('--workspace', result.output)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Verify that the correct error is displayed when the API Key is missing."""
        result = self.runner.invoke(main, ['--api-key', '', 'Olá'])
        self.assertIn('Error: Gemini API key not found', result.output)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    def test_setup_agent_config_skills_fallback(self):
        """Verify that setup_agent_config falls back to the CLI installation folder's .agents/skills if skills_path is empty."""
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=[]
        )
        self.assertIsNotNone(config.skills_paths)
        self.assertEqual(len(config.skills_paths), 1)
        self.assertTrue(config.skills_paths[0].endswith(os.path.join(".agents", "skills")))

    @patch('builtins.input', return_value='y')
    def test_cli_ask_user_handler_approve(self, mock_input):
        """Verify that the policy manager accepts 'y' for user confirmation."""
        mock_tool_call = MagicMock()
        mock_tool_call.name = "RUN_COMMAND"
        mock_tool_call.args = {"cmd": "dir"}
        
        approved = cli_ask_user_handler(mock_tool_call)
        self.assertTrue(approved)

    @patch('builtins.input', return_value='n')
    def test_cli_ask_user_handler_reject(self, mock_input):
        """Verify that the policy manager rejects 'n' for user confirmation."""
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
        """Verify that the basic prompt execution flow works and invokes the correct agents."""
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
        """Verify that the --silent flag is correctly propagated to the stream."""
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
        """Verify that references to @file are injected with the file content."""
        # Create temporary file for testing
        temp_file = "temp_test_file.txt"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("Temporary file test content.")
            
            prompt = f"Analise o arquivo @{temp_file} por favor."
            processed = preprocess_prompt(prompt)
            
            self.assertIn("=== FILE CONTENT: temp_test_file.txt", processed)
            self.assertIn("Temporary file test content.", processed)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_preprocess_prompt_skill_injection(self):
        """Verify that references to /skill are injected with the rules from SKILL.md."""
        # Create temporary skill
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
            
            self.assertIn("=== SKILL INSTRUCTIONS: test_skill", processed)
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
        """Verify that the agent configuration is successfully generated."""
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
        self.assertIsNotNone(config.skills_paths)
        self.assertEqual(len(config.skills_paths), 1)
        self.assertTrue(config.skills_paths[0].endswith(os.path.join(".agents", "skills")))

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_agent_config_missing_key(self):
        """Verify that ValueError is raised when the API Key is missing."""
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
        """Verify that new directive processors can be added without modifying existing code (OCP)."""
        import re
        from interfaces import DirectiveProcessor
        from parser import PromptPreprocessor
        
        class MockIssueDirectiveProcessor(DirectiveProcessor):
            def process(self, prompt: str, skills_paths=None):
                match = re.search(r'#issue-(\d+)', prompt)
                extra = []
                if match:
                    issue_id = match.group(1)
                    extra.append(f"=== ISSUE #{issue_id} DETAILS ===\nCorrigir bug de login no sistema.")
                return prompt, extra

        preprocessor = PromptPreprocessor(processors=[MockIssueDirectiveProcessor()])
        
        prompt = "Resolva a issue #issue-999"
        processed = preprocessor.preprocess(prompt)
        
        self.assertIn("=== ISSUE #999 DETAILS ===", processed)
        self.assertIn("Corrigir bug de login no sistema.", processed)

    @patch('repl.click.echo')
    def test_run_repl_exit_command(self, mock_echo):
        """Verify that the REPL exits and prints 'Exiting...' upon receiving /quit."""
        import asyncio
        from repl import run_repl
        from interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None) -> str:
                return "/quit"
                
        mock_agent = MagicMock()
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        mock_echo.assert_called_with(f"{Fore.YELLOW}Exiting...{Style.RESET_ALL}")

    def test_i18n_translation_keys(self):
        """Verify that i18n translation keys return correct messages for both en-us and pt-br."""
        i18n.set_language("en-us")
        en_msg = i18n.t("repl", "exiting")
        self.assertEqual(en_msg, "Exiting...")
        
        i18n.set_language("pt-br")
        pt_msg = i18n.t("repl", "exiting")
        self.assertEqual(pt_msg, "Saindo...")

    @patch('repl.click.echo')
    @patch('repl._get_repl_suggestions')
    def test_run_repl_displays_skills_limit(self, mock_get_repl_suggestions, mock_echo):
        """Verify that the REPL welcome banner prints local skills, limiting to 5 with an 'and more' suffix."""
        import asyncio
        from repl import run_repl
        from interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None) -> str:
                return "/quit"
                
        # Scenario 1: More than 5 skills (should limit and append 'and more')
        mock_get_repl_suggestions.return_value = ["/exit", "/quit", "/reset", "/s1", "/s2", "/s3", "/s4", "/s5", "/s6", "/s7"]
        mock_agent = MagicMock()
        
        i18n.set_language("en-us")
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        # Check if the individual skills and limit text are printed correctly
        any_match_s1_en = any(f"  {Fore.GREEN}/s1{Style.RESET_ALL}" == args[0] for args, _ in mock_echo.call_args_list)
        any_match_s5_en = any(f"  {Fore.GREEN}/s5{Style.RESET_ALL}" == args[0] for args, _ in mock_echo.call_args_list)
        any_match_limit_en = any(f"  ... and more" == args[0] for args, _ in mock_echo.call_args_list)
        
        self.assertTrue(any_match_s1_en)
        self.assertTrue(any_match_s5_en)
        self.assertTrue(any_match_limit_en)

        # Scenario 2: Portuguese switches correctly
        mock_echo.reset_mock()
        i18n.set_language("pt-br")
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        any_match_s1_pt = any(f"  {Fore.GREEN}/s1{Style.RESET_ALL}" == args[0] for args, _ in mock_echo.call_args_list)
        any_match_limit_pt = any(f"  ... e mais" == args[0] for args, _ in mock_echo.call_args_list)
        
        self.assertTrue(any_match_s1_pt)
        self.assertTrue(any_match_limit_pt)

    def test_get_repl_suggestions_fallback(self):
        """Verify that _get_repl_suggestions falls back to default folders if paths are empty or None."""
        from repl import _get_repl_suggestions
        
        suggestions_none = _get_repl_suggestions(None)
        self.assertIn("/gerar_skill_template", suggestions_none)
        self.assertIn("/gerenciar_deploy", suggestions_none)
        self.assertIn("/exit", suggestions_none)
        self.assertIn("/reset", suggestions_none)
        
        suggestions_empty = _get_repl_suggestions([])
        self.assertIn("/gerar_skill_template", suggestions_empty)

    def test_command_completer_pattern_backspace_and_filtering(self):
        """Verify that CommandCompleter with _PATTERN_CMD handles backspaces, spaces, middle of line slash, and filters commands properly."""
        from console_io import _PATTERN_CMD, CommandCompleter
        from prompt_toolkit.document import Document
        
        completer = CommandCompleter(["/exit", "/quit", "/reset", "/gerar_skill_template", "/gerenciar_deploy"], ignore_case=True, pattern=_PATTERN_CMD)
        
        # Test exact match of command typed completely
        doc1 = Document("/gerar")
        completions1 = list(completer.get_completions(doc1, None))
        self.assertEqual(len(completions1), 1)
        self.assertEqual(completions1[0].text, "/gerar_skill_template")
        
        # Test backspaced match (fewer letters)
        doc2 = Document("/gera")
        completions2 = list(completer.get_completions(doc2, None))
        self.assertEqual(len(completions2), 1)
        self.assertEqual(completions2[0].text, "/gerar_skill_template")
        
        # Test short pattern matching multiple choices
        doc3 = Document("/ger")
        completions3 = list(completer.get_completions(doc3, None))
        self.assertEqual(len(completions3), 2)
        self.assertIn("/gerar_skill_template", [c.text for c in completions3])
        self.assertIn("/gerenciar_deploy", [c.text for c in completions3])
        
        # Test non-slash input does not trigger suggestions
        doc4 = Document("gerar")
        completions4 = list(completer.get_completions(doc4, None))
        self.assertEqual(len(completions4), 0)

        # Test trailing space input does not trigger suggestions (fixes space bug)
        doc5 = Document("Olá ")
        completions5 = list(completer.get_completions(doc5, None))
        self.assertEqual(len(completions5), 0)

        # Test middle of the line slash command suggestion (middle matching)
        doc6 = Document("Olá /ger")
        completions6 = list(completer.get_completions(doc6, None))
        self.assertEqual(len(completions6), 2)
        self.assertIn("/gerar_skill_template", [c.text for c in completions6])
        self.assertIn("/gerenciar_deploy", [c.text for c in completions6])

if __name__ == '__main__':
    unittest.main()
