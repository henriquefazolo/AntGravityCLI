import unittest
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
import os
from colorama import Fore, Style

# Import the CLI and functions to test
from antgravity_cli.main import main
from antgravity_cli.runner import run_cli
from antgravity_cli.config import setup_agent_config
from antgravity_cli.parser import preprocess_prompt
from antgravity_cli.handlers import cli_ask_user_handler
from antgravity_cli.console_io import ConsoleOutputWriter
from antgravity_cli import i18n

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
        """Verify that setup_agent_config resolves both custom -k paths and the native CLI installation folder's .agents/skills."""
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=["C:\\some\\other\\path"]
        )
        self.assertIsNotNone(config.skills_paths)
        self.assertEqual(len(config.skills_paths), 2)
        self.assertIn("C:\\some\\other\\path", config.skills_paths)
        self.assertTrue(config.skills_paths[1].endswith(os.path.join(".agents", "skills")))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    def test_setup_agent_config_skills_normalization(self):
        """Verify that setup_agent_config normalizes skills paths to absolute paths and deduplicates them."""
        # Mix of relative, absolute, and duplicate paths
        from antgravity_cli.utils import get_base_path
        base_dir = get_base_path()
        cli_skills_dir = os.path.join(base_dir, ".agents", "skills")
        
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=[
                ".",
                os.path.abspath("."),
                cli_skills_dir,
                cli_skills_dir
            ]
        )
        self.assertIsNotNone(config.skills_paths)
        # Deduplicated output length should be 2: absolute path of '.' and absolute path of physical package skills dir
        self.assertEqual(len(config.skills_paths), 2)
        self.assertEqual(config.skills_paths[0], os.path.abspath("."))
        self.assertEqual(config.skills_paths[1], cli_skills_dir)

    def test_i18n_formatting_warning(self):
        """Verify that i18n.t raises a UserWarning when format arguments are mismatched."""
        from antgravity_cli import i18n
        
        # We call translation with mismatched kwargs to force KeyError
        with patch('antgravity_cli.i18n._load_translations') as mock_load:
            mock_load.return_value = {"test_key": "Hello {name}"}
            
            # Missing format arguments (should raise warning)
            with self.assertWarns(UserWarning) as w:
                res = i18n.t("test_module", "test_key", wrong_arg="test")
            
            self.assertEqual(res, "Hello {name}") # Returns raw message
            self.assertIn("Format arguments mismatch", str(w.warning))

    def test_utils_get_base_path_frozen(self):
        """Verify that get_base_path returns sys._MEIPASS when running as frozen executable."""
        import sys
        from antgravity_cli import utils
        
        # 1. Normal execution (unfrozen)
        with patch.object(sys, 'frozen', False, create=True):
            normal_path = utils.get_base_path()
            self.assertEqual(normal_path, os.path.dirname(os.path.abspath(utils.__file__)))
            
        # 2. Standalone frozen execution
        with patch.object(sys, 'frozen', True, create=True), \
             patch.object(sys, '_MEIPASS', "C:\\mock_meipass", create=True):
            frozen_path = utils.get_base_path()
            self.assertEqual(frozen_path, "C:\\mock_meipass")

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

    @patch('antgravity_cli.runner.Agent')
    @patch('antgravity_cli.config.LocalAgentConfig')
    @patch('antgravity_cli.runner.stream_chat_response')
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

    @patch('antgravity_cli.runner.Agent')
    @patch('antgravity_cli.config.LocalAgentConfig')
    @patch('antgravity_cli.runner.stream_chat_response')
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
        from antgravity_cli.interfaces import DirectiveProcessor
        from antgravity_cli.parser import PromptPreprocessor
        
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

    @patch('antgravity_cli.repl.click.echo')
    def test_run_repl_exit_command(self, mock_echo):
        """Verify that the REPL exits and prints 'Exiting...' upon receiving /quit."""
        import asyncio
        from antgravity_cli.repl import run_repl
        from antgravity_cli.interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
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

    @patch('antgravity_cli.repl.click.echo')
    @patch('antgravity_cli.repl._get_repl_suggestions')
    def test_run_repl_displays_skills_limit(self, mock_get_repl_suggestions, mock_echo):
        """Verify that the REPL welcome banner prints local skills, limiting to 5 with an 'and more' suffix."""
        import asyncio
        from antgravity_cli.repl import run_repl
        from antgravity_cli.interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
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

    @patch('antgravity_cli.repl.click.echo')
    @patch('antgravity_cli.repl._get_repl_suggestions')
    def test_run_repl_displays_ant_art_logo(self, mock_get_repl_suggestions, mock_echo):
        """Verify that the welcome banner prints the Option 1 ant logo correctly."""
        import asyncio
        from antgravity_cli.repl import run_repl
        from antgravity_cli.interfaces import InputReader
        
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
                return "/quit"
                
        mock_get_repl_suggestions.return_value = ["/exit", "/quit", "/reset"]
        mock_agent = MagicMock()
        
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        # Verify the logo lines are in the printed output
        logo_line_1 = f"  {Fore.CYAN}▄▀▀▄       ▄▀▀▄{Style.RESET_ALL}"
        logo_line_2 = f"   {Fore.CYAN}▀▄ ▀▄   ▄▀ ▄▀{Style.RESET_ALL}"
        logo_line_3 = f"    {Fore.BLUE}▄█████████▄{Style.RESET_ALL}"
        
        self.assertTrue(any(logo_line_1 == args[0] for args, _ in mock_echo.call_args_list))
        self.assertTrue(any(logo_line_2 == args[0] for args, _ in mock_echo.call_args_list))
        self.assertTrue(any(logo_line_3 == args[0] for args, _ in mock_echo.call_args_list))

    def test_get_repl_suggestions_fallback(self):
        """Verify that _get_repl_suggestions falls back to default folders if paths are empty or None."""
        from antgravity_cli.repl import _get_repl_suggestions
        
        suggestions_none = _get_repl_suggestions(None)
        self.assertIn("/generate_skill_template", suggestions_none)
        self.assertIn("/exit", suggestions_none)
        self.assertIn("/reset", suggestions_none)
        
        suggestions_empty = _get_repl_suggestions([])
        self.assertIn("/generate_skill_template", suggestions_empty)

    def test_command_completer_pattern_backspace_and_filtering(self):
        """Verify that CommandCompleter with _PATTERN_CMD handles backspaces, spaces, middle of line slash, and filters commands properly."""
        from antgravity_cli.console_io import _PATTERN_CMD, CommandCompleter
        from prompt_toolkit.document import Document
        
        completer = CommandCompleter(["/exit", "/quit", "/reset", "/generate_skill_template", "/gerund"], ignore_case=True, pattern=_PATTERN_CMD)
        
        # Test exact match of command typed completely
        doc1 = Document("/gener")
        completions1 = list(completer.get_completions(doc1, None))
        self.assertEqual(len(completions1), 1)
        self.assertEqual(completions1[0].text, "/generate_skill_template")
        
        # Test backspaced match (fewer letters)
        doc2 = Document("/gene")
        completions2 = list(completer.get_completions(doc2, None))
        self.assertEqual(len(completions2), 1)
        self.assertEqual(completions2[0].text, "/generate_skill_template")
        
        # Test short pattern matching multiple choices
        doc3 = Document("/ge")
        completions3 = list(completer.get_completions(doc3, None))
        self.assertEqual(len(completions3), 2)
        self.assertIn("/generate_skill_template", [c.text for c in completions3])
        self.assertIn("/gerund", [c.text for c in completions3])
        
        # Test non-slash input does not trigger suggestions
        doc4 = Document("generate")
        completions4 = list(completer.get_completions(doc4, None))
        self.assertEqual(len(completions4), 0)

        # Test trailing space input does not trigger suggestions (fixes space bug)
        doc5 = Document("Olá ")
        completions5 = list(completer.get_completions(doc5, None))
        self.assertEqual(len(completions5), 0)

        # Test middle of the line slash command suggestion (middle matching)
        doc6 = Document("Olá /ge")
        completions6 = list(completer.get_completions(doc6, None))
        self.assertEqual(len(completions6), 2)
        self.assertIn("/generate_skill_template", [c.text for c in completions6])
        self.assertIn("/gerund", [c.text for c in completions6])

    @patch('antgravity_cli.main.run_cli')
    @patch.dict(os.environ, {
        'GEMINI_MODEL': 'gemini-custom',
        'ANTGRAVITY_LANG': 'pt-br',
        'ANTGRAVITY_YOLO': '1',
        'GEMINI_API_KEY': 'envvar-api-key'
    })
    def test_cli_environment_variables(self, mock_run_cli):
        """Verify that CLI options fall back to environment variables correctly."""
        result = self.runner.invoke(main, [])
        self.assertEqual(result.exit_code, 0)
        
        # We check the arguments passed to run_cli
        mock_run_cli.assert_called_once()
        args, kwargs = mock_run_cli.call_args
        # args map: prompt, model, yolo, workspace, system_instruction, api_key, skills_path
        self.assertEqual(args[0], None)  # prompt
        self.assertEqual(args[1], 'gemini-custom')  # model
        self.assertEqual(args[2], True)  # yolo
        self.assertEqual(args[5], 'envvar-api-key')  # api_key
        self.assertEqual(kwargs.get('language'), 'pt-br')  # language

    @patch('dotenv.load_dotenv')
    @patch('os.path.exists')
    @patch('antgravity_cli.utils.get_base_path')
    def test_env_loading_precedence(self, mock_get_base_path, mock_exists, mock_load_dotenv):
        """Verify that .env files are loaded from the base installation and CWD with correct overrides."""
        import importlib
        import antgravity_cli.main as main_module

        mock_get_base_path.return_value = "C:\\base_dir"
        
        # Simulate both .env files existing, but restrict to .env files to avoid side effects on reload
        mock_exists.side_effect = lambda path: path.endswith('.env')
        
        # Reload main module to trigger execution of module-level code
        importlib.reload(main_module)
        
        # Assertions
        # Should call load_dotenv twice: first for base, then for CWD (with override=True)
        self.assertEqual(mock_load_dotenv.call_count, 2)
        
        calls = mock_load_dotenv.call_args_list
        # First call: base_env path
        self.assertEqual(calls[0][0][0], os.path.join("C:\\base_dir", ".env"))
        
        # Second call: CWD env path, with override=True
        self.assertEqual(calls[1][0][0], os.path.abspath(".env"))
        self.assertEqual(calls[1][1].get('override'), True)

    @patch('antgravity_cli.main.run_cli')
    @patch.dict(os.environ, {
        'GEMINI_MODEL': 'gemini-custom',
        'ANTGRAVITY_LANG': 'pt-br',
        'ANTGRAVITY_YOLO': '1',
        'GEMINI_API_KEY': 'envvar-api-key',
        'ANTGRAVITY_WORKSPACE': os.path.abspath("."),
        'ANTGRAVITY_SYSTEM_INSTRUCTION': 'custom-instruction',
        'ANTGRAVITY_SKILLS_PATH': os.path.abspath("."),
        'ANTGRAVITY_SILENT': '1',
        'ANTGRAVITY_VERBOSE': '1'
    })
    def test_cli_environment_variables_comprehensive(self, mock_run_cli):
        """Verify that all CLI options fall back to environment variables correctly."""
        result = self.runner.invoke(main, [])
        self.assertEqual(result.exit_code, 0)
        
        mock_run_cli.assert_called_once()
        args, kwargs = mock_run_cli.call_args
        # args map: prompt, model, yolo, workspace, system_instruction, api_key, skills_path
        self.assertEqual(args[0], None)  # prompt
        self.assertEqual(args[1], 'gemini-custom')  # model
        self.assertEqual(args[2], True)  # yolo
        self.assertEqual(args[3], (os.path.abspath("."),))  # workspace (as tuple)
        self.assertEqual(args[4], 'custom-instruction')  # system_instruction
        self.assertEqual(args[5], 'envvar-api-key')  # api_key
        self.assertEqual(args[6], (os.path.abspath("."),))  # skills_path (as tuple)
        self.assertEqual(kwargs.get('silent'), True)  # silent
        self.assertEqual(kwargs.get('verbose'), True)  # verbose
        self.assertEqual(kwargs.get('language'), 'pt-br')  # language

    @patch('dotenv.load_dotenv')
    @patch('os.path.exists')
    @patch('sys.argv', ['antgravity_cli/main.py', '-e', 'custom_env_file.env'])
    def test_env_loading_custom_file(self, mock_exists, mock_load_dotenv):
        """Verify that passing -e loads only the custom env file and overrides standard envs."""
        import importlib
        import antgravity_cli.main as main_module

        # Simulate custom file existing
        mock_exists.side_effect = lambda path: True if path == 'custom_env_file.env' else False
        
        # Reload main module to trigger execution of module-level code
        importlib.reload(main_module)
        
        # Assertions
        # Should call load_dotenv once with the custom file path and override=True
        mock_load_dotenv.assert_called_once_with('custom_env_file.env', override=True)

    def test_get_workspace_files_and_folders(self):
        """Verify that get_workspace_files_and_folders correctly finds, formats, and filters workspace files and folders."""
        import tempfile
        from antgravity_cli.utils import get_workspace_files_and_folders

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            os.makedirs(os.path.join(tmpdir, "folder1"))
            os.makedirs(os.path.join(tmpdir, ".git"))
            os.makedirs(os.path.join(tmpdir, "venv"))
            os.makedirs(os.path.join(tmpdir, "__pycache__"))
            
            with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
                f.write("test")
            with open(os.path.join(tmpdir, "folder1", "file2.txt"), "w") as f:
                f.write("test")
            with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
                f.write("test")
            with open(os.path.join(tmpdir, "venv", "activate"), "w") as f:
                f.write("test")
            with open(os.path.join(tmpdir, "__pycache__", "test.pyc"), "w") as f:
                f.write("test")
                
            res = get_workspace_files_and_folders(tmpdir)
            
            # Expected relative paths normalized with forward slashes, directories ending with '/'
            # Should contain: 'file1.txt', 'folder1/', 'folder1/file2.txt'
            # Should NOT contain: '.git/', 'venv/', '__pycache__/' or files within them
            self.assertIn("file1.txt", res)
            self.assertIn("folder1/", res)
            self.assertIn("folder1/file2.txt", res)
            
            self.assertNotIn(".git/", res)
            self.assertNotIn(".git/config", res)
            self.assertNotIn("venv/", res)
            self.assertNotIn("venv/activate", res)
            self.assertNotIn("__pycache__/", res)
            self.assertNotIn("__pycache__/test.pyc", res)

    def test_ant_completer(self):
        """Verify that AntCompleter handles slash commands and at-sign file completions correctly."""
        from antgravity_cli.console_io import AntCompleter
        from prompt_toolkit.document import Document
        
        completer = AntCompleter(
            command_suggestions=["/exit", "/generate_skill_template"],
            file_suggestions=["README.md", "antgravity_cli/main.py"]
        )
        
        # Test command completions
        doc1 = Document("/ex")
        completions1 = list(completer.get_completions(doc1, None))
        self.assertEqual(len(completions1), 1)
        self.assertEqual(completions1[0].text, "/exit")
        
        # Test file completions matching prefix
        doc2 = Document("@REA")
        completions2 = list(completer.get_completions(doc2, None))
        self.assertEqual(len(completions2), 1)
        self.assertEqual(completions2[0].text, "@README.md")
        
        # Test file completions list all on typing '@' only
        doc3 = Document("@")
        completions3 = list(completer.get_completions(doc3, None))
        self.assertEqual(len(completions3), 2)
        texts = [c.text for c in completions3]
        self.assertIn("@README.md", texts)
        self.assertIn("@antgravity_cli/main.py", texts)
        
        # Test mid-line file completions
        doc4 = Document("Check @ant")
        completions4 = list(completer.get_completions(doc4, None))
        self.assertEqual(len(completions4), 1)
        self.assertEqual(completions4[0].text, "@antgravity_cli/main.py")

if __name__ == '__main__':
    unittest.main()


