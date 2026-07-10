import unittest
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
import os
import asyncio
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
        """Verify that setup_agent_config resolves both custom -k paths and the native CLI installation folder's builtin/skills."""
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
        self.assertTrue(config.skills_paths[1].endswith(os.path.join("builtin", "skills")))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    def test_setup_agent_config_skills_normalization(self):
        """Verify that setup_agent_config normalizes skills paths to absolute paths and deduplicates them."""
        # Mix of relative, absolute, and duplicate paths
        from antgravity_cli.utils import get_base_path
        base_dir = get_base_path()
        cli_skills_dir = os.path.join(base_dir, "builtin", "skills")
        
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

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    @patch('antgravity_cli.subagents.discover_subagents_in_paths')
    def test_setup_agent_config_registers_subagent_tools(self, mock_discover):
        """Verify that setup_agent_config discovers subagent tools and registers them as dummy tools."""
        from google.antigravity.types import SubagentConfig
        
        # Setup mock subagent that requires a custom tool
        mock_subagent = SubagentConfig(
            name="test_subagent",
            description="Test subagent requiring a custom tool",
            system_instructions="instructions",
            capabilities=None,
            tools=["run_mock_custom_tool"]
        )
        mock_discover.return_value = [mock_subagent]
        
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=[]
        )
        
        # Verify tools are registered on the main config
        self.assertIsNotNone(config.tools)
        self.assertEqual(len(config.tools), 1)
        self.assertEqual(config.tools[0].__name__, "run_mock_custom_tool")
        
        # Verify we can execute the dummy tool
        result = config.tools[0]()
        self.assertEqual(result, "Placeholder execution")


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
    @patch('os.path.isdir')
    def test_setup_agent_config_success(self, mock_isdir):
        """Verify that the agent configuration is successfully generated."""
        # Force workspace check to find no directories, only package path exists
        mock_isdir.side_effect = lambda path: True if "builtin" in path else False

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
        self.assertTrue(config.skills_paths[0].endswith(os.path.join("builtin", "skills")))

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
        'ANTGRAVITY_VERBOSE': '1',
        'ANTGRAVITY_VERBOSE_SUBAGENTS': '1'
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
        self.assertEqual(kwargs.get('verbose_subagents'), True)  # verbose_subagents
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
        """Verify that AntCompleter handles slash commands, at-sign file completions, and colon subagent completions correctly."""
        from antgravity_cli.console_io import AntCompleter
        from prompt_toolkit.document import Document
        
        completer = AntCompleter(
            command_suggestions=["/exit", "/generate_skill_template"],
            file_suggestions=["README.md", "antgravity_cli/main.py"],
            subagent_suggestions=["test_helper", "log_analyzer"]
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

        # Test middle-of-path file completions (substring match)
        doc5 = Document("@cli")
        completions5 = list(completer.get_completions(doc5, None))
        self.assertEqual(len(completions5), 1)
        self.assertEqual(completions5[0].text, "@antgravity_cli/main.py")

        # Test prioritization of prefix match over middle/substring match
        completer_prio = AntCompleter(
            command_suggestions=[],
            file_suggestions=["antgravity_cli/main.py", "cli_test.py"]
        )
        doc6 = Document("@cli")
        completions6 = list(completer_prio.get_completions(doc6, None))
        self.assertEqual(len(completions6), 2)
        # prefix match 'cli_test.py' must come first
        self.assertEqual(completions6[0].text, "@cli_test.py")
        self.assertEqual(completions6[1].text, "@antgravity_cli/main.py")

        # Test subagent completions matching prefix
        doc7 = Document(":log")
        completions7 = list(completer.get_completions(doc7, None))
        self.assertEqual(len(completions7), 1)
        self.assertEqual(completions7[0].text, ":log_analyzer")

        # Test subagent completions list all on typing ':' only
        doc8 = Document(":")
        completions8 = list(completer.get_completions(doc8, None))
        self.assertEqual(len(completions8), 2)
        sub_texts = [c.text for c in completions8]
        self.assertIn(":test_helper", sub_texts)
        self.assertIn(":log_analyzer", sub_texts)

        # Test mid-line subagent completions
        doc9 = Document("Please call :te")
        completions9 = list(completer.get_completions(doc9, None))
        self.assertEqual(len(completions9), 1)
        self.assertEqual(completions9[0].text, ":test_helper")

    def test_command_handlers_registry(self):
        """Verify that commands registry correctly returns maps and triggers."""
        from antgravity_cli.builtin.commands import get_command_map, get_command_triggers
        
        cmd_map = get_command_map()
        self.assertIn("/exit", cmd_map)
        self.assertIn("/quit", cmd_map)
        self.assertIn("/reset", cmd_map)
        self.assertIn("/help", cmd_map)
        self.assertIn("?", cmd_map)
        self.assertIn("/ants", cmd_map)
        self.assertIn("/subagents", cmd_map)
        self.assertIn("/disable_skill", cmd_map)
        self.assertIn("/enable_skill", cmd_map)
        self.assertIn("/disable_agent", cmd_map)
        self.assertIn("/enable_agent", cmd_map)
        
        triggers = get_command_triggers()
        self.assertEqual(triggers, [
            "/ants",
            "/disable_agent",
            "/disable_skill",
            "/enable_agent",
            "/enable_skill",
            "/exit",
            "/help",
            "/quit",
            "/reset",
            "/subagents",
            "?"
        ])

    @patch('antgravity_cli.builtin.commands.help.click.echo')
    def test_help_command_handler(self, mock_echo):
        """Verify that HelpCommand displays commands, skills, and subagents, and returns True."""
        import asyncio
        from antgravity_cli.builtin.commands.help import HelpCommand
        from google.antigravity.types import SubagentConfig
        
        cmd = HelpCommand()
        self.assertEqual(cmd.description_key, "command_help_desc")
        
        mock_agent = MagicMock()
        mock_sub = SubagentConfig(name="MockSub", description="Desc")
        mock_agent.config.subagents = [mock_sub]
        mock_agent.config.skills_paths = []
        
        result = asyncio.run(cmd.execute(mock_agent))
        self.assertTrue(result)
        self.assertGreater(mock_echo.call_count, 3)

    @patch('antgravity_cli.builtin.commands.ants.click.echo')
    def test_ants_command_handler(self, mock_echo):
        """Verify that AntsCommand displays subagent capabilities and returns True."""
        import asyncio
        from antgravity_cli.builtin.commands.ants import AntsCommand
        from google.antigravity.types import SubagentConfig
        
        cmd = AntsCommand()
        self.assertEqual(cmd.description_key, "command_ants_desc")
        
        mock_agent = MagicMock()
        mock_sub = SubagentConfig(name="MockSub", description="Desc")
        mock_agent.config.subagents = [mock_sub]
        
        result = asyncio.run(cmd.execute(mock_agent))
        self.assertTrue(result)
        self.assertGreater(mock_echo.call_count, 1)

    @patch('antgravity_cli.builtin.commands.exit.click.echo')
    def test_exit_command_handler(self, mock_echo):
        """Verify that ExitCommand displays the exit message and returns False."""
        import asyncio
        from antgravity_cli.builtin.commands.exit import ExitCommand
        
        cmd = ExitCommand()
        self.assertEqual(cmd.description_key, "command_exit_desc")
        
        result = asyncio.run(cmd.execute(MagicMock()))
        self.assertFalse(result)
        self.mock_echo = mock_echo # keep reference
        mock_echo.assert_called_once()

    @patch('antgravity_cli.builtin.commands.reset.click.echo')
    def test_reset_command_handler(self, mock_echo):
        """Verify that ResetCommand clears history and returns True."""
        import asyncio
        from antgravity_cli.builtin.commands.reset import ResetCommand
        
        cmd = ResetCommand()
        self.assertEqual(cmd.description_key, "command_reset_desc")
        
        mock_agent = MagicMock()
        result = asyncio.run(cmd.execute(mock_agent))
        self.assertTrue(result)
        mock_agent.conversation.clear_history.assert_called_once()
        mock_echo.assert_called_once()

    def test_parse_agent_md_full(self):
        """Verify that parse_agent_md correctly parses YAML frontmatter and body."""
        from antgravity_cli.subagents import parse_agent_md
        from google.antigravity.types import BuiltinTools
        
        content = """---
name: "TestAgent"
description: "A helper agent for testing."
capabilities:
  enabled_tools:
    - VIEW_FILE
    - EDIT_FILE
tools:
  - my_custom_tool
---
This is the system instructions body.
Line 2 of instructions."""

        config = parse_agent_md(content)
        self.assertEqual(config["name"], "TestAgent")
        self.assertEqual(config["description"], "A helper agent for testing.")
        self.assertIn("This is the system instructions body.", config["system_instructions"])
        self.assertIn("Line 2 of instructions.", config["system_instructions"])
        self.assertEqual(config["tools"], ["my_custom_tool"])
        self.assertIsNotNone(config["capabilities"])
        self.assertEqual(config["capabilities"].enabled_tools, [BuiltinTools.VIEW_FILE, BuiltinTools.EDIT_FILE])
        self.assertIsNone(config["capabilities"].disabled_tools)

    def test_discover_subagents_in_paths(self):
        """Verify that discover_subagents_in_paths scans folder and instantiates SubagentConfig."""
        import tempfile
        import shutil
        from antgravity_cli.subagents import discover_subagents_in_paths
        
        tmp_dir = tempfile.mkdtemp()
        subagent_dir = os.path.join(tmp_dir, "my_subagent")
        os.makedirs(subagent_dir)
        
        agent_md_content = """---
name: "LogAnalyzer"
description: "Analyses logs."
---
Log instructions."""
        
        with open(os.path.join(subagent_dir, "AGENT.md"), "w", encoding="utf-8") as f:
            f.write(agent_md_content)
            
        try:
            subagents = discover_subagents_in_paths([tmp_dir])
            self.assertEqual(len(subagents), 1)
            sub = subagents[0]
            self.assertEqual(sub.name, "LogAnalyzer")
            self.assertEqual(sub.description, "Analyses logs.")
            self.assertEqual(sub.system_instructions, "Log instructions.")
            self.assertEqual(sub.tools, [])
            self.assertIsNone(sub.capabilities)
        finally:
            shutil.rmtree(tmp_dir)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    @patch('antgravity_cli.config.os.path.isdir')
    @patch('antgravity_cli.subagents.discover_subagents_in_paths')
    def test_setup_agent_config_subagents(self, mock_discover, mock_isdir):
        """Verify that setup_agent_config resolves and injects discovered subagents."""
        from antgravity_cli.config import setup_agent_config
        from google.antigravity.types import SubagentConfig
        
        mock_isdir.side_effect = lambda path: True if "subagents" in path or "builtin" in path else False
        mock_subagent = SubagentConfig(name="MockSub", description="Desc", system_instructions="Inst")
        mock_discover.return_value = [mock_subagent]
        
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=[]
        )
        self.assertIsNotNone(config.subagents)
        self.assertEqual(len(config.subagents), 1)
        self.assertEqual(config.subagents[0].name, "MockSub")

    def test_get_active_subagent_name(self):
        """Verify that get_active_subagent_name extracts the subagent name from history."""
        from antgravity_cli.repl import get_active_subagent_name
        from google.antigravity import types
        
        # Scenario 1: Empty history
        mock_agent = MagicMock()
        mock_agent.conversation.history = []
        self.assertIsNone(get_active_subagent_name(mock_agent))
        
        # Scenario 2: History with no start_subagent call
        step1 = types.Step(
            id="1",
            step_index=0,
            type=types.StepType.TOOL_CALL,
            source=types.StepSource.MODEL,
            target=types.StepTarget.USER
        )
        mock_agent.conversation.history = [step1]
        self.assertIsNone(get_active_subagent_name(mock_agent))
        
        # Scenario 3: History with start_subagent call
        call = types.ToolCall(id="tc1", name="start_subagent", args={"agent_name": "TestHelper"})
        step2 = types.Step(
            id="2",
            step_index=1,
            type=types.StepType.TOOL_CALL,
            source=types.StepSource.MODEL,
            target=types.StepTarget.USER,
            tool_calls=[call]
        )
        mock_agent.conversation.history = [step1, step2]
        self.assertEqual(get_active_subagent_name(mock_agent), "TestHelper")

    @patch('antgravity_cli.init_project.click.prompt')
    @patch('antgravity_cli.init_project.click.confirm')
    @patch('antgravity_cli.init_project.click.echo')
    def test_init_project(self, mock_echo, mock_confirm, mock_prompt):
        """Verify that run_init correctly sets up workspace directories and .env file."""
        from antgravity_cli.init_project import run_init
        import tempfile
        import shutil
        
        mock_prompt.side_effect = lambda text, **kwargs: {
            "Gemini API Key (leave empty to skip)": "test_api_key",
            "Gemini Model": "gemini-3.1-flash-lite",
            "Language (en-us, pt-br)": "pt-br"
        }.get(text, "default_val")
        mock_confirm.return_value = True
        
        # Run in a clean temp directory
        tmp_dir = tempfile.mkdtemp()
        orig_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            run_init()
            
            # Check directories
            self.assertTrue(os.path.isdir(".agents"))
            self.assertTrue(os.path.isdir(os.path.join(".agents", "skills")))
            self.assertTrue(os.path.isdir(os.path.join(".agents", "subagents")))
            
            # Check AGENTS.md
            self.assertTrue(os.path.isfile(os.path.join(".agents", "AGENTS.md")))
            
            # Check skill_example and subagent_example templates
            self.assertTrue(os.path.isfile(os.path.join(".agents", "skills", "skill_example", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(".agents", "subagents", "subagent_example", "AGENT.md")))
            
            # Check .env file
            self.assertTrue(os.path.isfile(".env"))
            with open(".env", "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("GEMINI_API_KEY=test_api_key", content)
                self.assertIn("GEMINI_MODEL=gemini-3.1-flash-lite", content)
                self.assertIn("ANTGRAVITY_LANG=pt-br", content)
                self.assertIn("ANTGRAVITY_YOLO=true", content)
        finally:
            os.chdir(orig_cwd)
            shutil.rmtree(tmp_dir)

    @patch('antgravity_cli.builtin.commands.disable_skill.click.echo')
    def test_disable_enable_skill_command(self, mock_echo):
        """Verify that DisableSkillCommand and EnableSkillCommand update agent._disabled_skills."""
        import asyncio
        from antgravity_cli.builtin.commands.disable_skill import DisableSkillCommand
        from antgravity_cli.builtin.commands.enable_skill import EnableSkillCommand
        
        mock_agent = MagicMock()
        mock_agent.config.skills_paths = []
        mock_agent._disabled_skills = set()
        
        # Test disabling
        cmd_disable = DisableSkillCommand()
        self.assertEqual(cmd_disable.description_key, "command_disable_skill_desc")
        res = asyncio.run(cmd_disable.execute(mock_agent, context="create_txt_file"))
        self.assertTrue(res)
        self.assertIn("create_txt_file", mock_agent._disabled_skills)
        
        # Test enabling
        cmd_enable = EnableSkillCommand()
        self.assertEqual(cmd_enable.description_key, "command_enable_skill_desc")
        res = asyncio.run(cmd_enable.execute(mock_agent, context="create_txt_file"))
        self.assertTrue(res)
        self.assertNotIn("create_txt_file", mock_agent._disabled_skills)

        # Test disabling with prefix '/'
        res = asyncio.run(cmd_disable.execute(mock_agent, context="/create_txt_file"))
        self.assertTrue(res)
        self.assertIn("create_txt_file", mock_agent._disabled_skills)

        # Test enabling with prefix '/'
        res = asyncio.run(cmd_enable.execute(mock_agent, context="/create_txt_file"))
        self.assertTrue(res)
        self.assertNotIn("create_txt_file", mock_agent._disabled_skills)

    @patch('antgravity_cli.builtin.commands.disable_agent.click.echo')
    def test_disable_enable_agent_command(self, mock_echo):
        """Verify that DisableAgentCommand and EnableAgentCommand update agent._disabled_subagents."""
        import asyncio
        from antgravity_cli.builtin.commands.disable_agent import DisableAgentCommand
        from antgravity_cli.builtin.commands.enable_agent import EnableAgentCommand
        
        mock_agent = MagicMock()
        mock_agent.config.workspaces = []
        mock_agent._disabled_subagents = set()
        
        # Test disabling
        cmd_disable = DisableAgentCommand()
        self.assertEqual(cmd_disable.description_key, "command_disable_agent_desc")
        res = asyncio.run(cmd_disable.execute(mock_agent, context="LogAnalyzer"))
        self.assertTrue(res)
        self.assertIn("LogAnalyzer", mock_agent._disabled_subagents)
        
        # Test enabling
        cmd_enable = EnableAgentCommand()
        self.assertEqual(cmd_enable.description_key, "command_enable_agent_desc")
        res = asyncio.run(cmd_enable.execute(mock_agent, context="LogAnalyzer"))
        self.assertTrue(res)
        self.assertNotIn("LogAnalyzer", mock_agent._disabled_subagents)

        # Test disabling with prefix ':'
        res = asyncio.run(cmd_disable.execute(mock_agent, context=":LogAnalyzer"))
        self.assertTrue(res)
        self.assertIn("LogAnalyzer", mock_agent._disabled_subagents)

        # Test enabling with prefix ':'
        res = asyncio.run(cmd_enable.execute(mock_agent, context=":LogAnalyzer"))
        self.assertTrue(res)
        self.assertNotIn("LogAnalyzer", mock_agent._disabled_subagents)

    def test_preprocess_prompt_excludes_disabled_skills(self):
        """Verify that preprocess_prompt does not load instructions for a disabled skill."""
        from antgravity_cli.parser import preprocess_prompt
        import tempfile
        import shutil
        
        tmp_dir = tempfile.mkdtemp()
        skill_dir = os.path.join(tmp_dir, "test_skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("Secret Instructions")
            
        try:
            # When active/enabled:
            prompt1 = preprocess_prompt("Please run /test_skill", skills_paths=[tmp_dir])
            self.assertIn("Secret Instructions", prompt1)
            
            # When disabled:
            prompt2 = preprocess_prompt("Please run /test_skill", skills_paths=[tmp_dir], disabled_skills={"test_skill"})
            self.assertNotIn("Secret Instructions", prompt2)
        finally:
            shutil.rmtree(tmp_dir)

    def test_suggestions_exclude_templates(self):
        """Verify that skill_example and subagent_example are excluded from autocompletion."""
        from antgravity_cli.repl import _get_repl_suggestions
        import tempfile
        import shutil
        
        # Test skill_example exclusion in _get_repl_suggestions
        tmp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp_dir, "skill_example"))
        with open(os.path.join(tmp_dir, "skill_example", "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("test")
            
        try:
            suggestions = _get_repl_suggestions([tmp_dir])
            self.assertNotIn("/skill_example", suggestions)
        finally:
            shutil.rmtree(tmp_dir)

    @patch('antgravity_cli.repl.ConsoleOutputWriter')
    def test_stream_chat_response_verbose_subagents(self, mock_writer_class):
        """Verify that stream_chat_response formats subagent chunks under verbose_subagents."""
        import asyncio
        from antgravity_cli.repl import stream_chat_response
        from google.antigravity.types import Thought, Text, ToolCall, ToolResult
        
        mock_writer = mock_writer_class.return_value
        mock_agent = MagicMock()
        
        # Mock step in history representing a subagent step
        class DummyStep:
            def __init__(self, step_index, trajectory_id):
                self.step_index = step_index
                self.trajectory_id = trajectory_id
                self.tool_calls = []
                
        # Mock active subagent start tool call
        start_call_step = DummyStep(0, "parent-traj")
        subagent_tool_call = MagicMock()
        subagent_tool_call.name = "start_subagent"
        subagent_tool_call.args = {"name": "TestSubagent"}
        start_call_step.tool_calls = [subagent_tool_call]
        
        subagent_step = DummyStep(1, "subagent-traj")
        subagent_tool_call_exec = MagicMock()
        subagent_tool_call_exec.name = "read_file"
        subagent_tool_call_exec.id = "t1"
        subagent_step.tool_calls = [subagent_tool_call_exec]
        
        mock_agent.conversation.history = [start_call_step, subagent_step]
        mock_agent.conversation.connection._main_trajectory_id = "parent-traj"
        
        # Mock connection response yielding a Thought chunk from the subagent
        mock_response = MagicMock()
        async def mock_chunks():
            yield Thought(step_index=1, text="Subagent logic thoughts")
            yield Text(step_index=1, text="Subagent output text")
            yield ToolCall(id="t1", name="read_file", args={"path": "a.txt"})
            yield ToolResult(id="t1", name="read_file", result="content")
            
        mock_response.chunks = mock_chunks()
        
        async def mock_chat(prompt):
            return mock_response
        mock_agent.chat = mock_chat
        
        # Test with verbose_subagents=True
        mock_writer.reset_mock()
        asyncio.run(stream_chat_response(
            mock_agent, "test", writer=mock_writer, silent=False, verbose=False, verbose_subagents=True
        ))
        
        # Assert subagent thoughts, tool calls, and results are written with prefix
        mock_writer.write_thought.assert_called_once_with("[TestSubagent] Subagent logic thoughts")
        mock_writer.write_tool_call.assert_called_once_with("[TestSubagent] read_file", {"path": "a.txt"})
        mock_writer.write_tool_result.assert_called_once_with("[TestSubagent] read_file", "content", None)
        
        # Test with verbose_subagents=False
        mock_writer.reset_mock()
        mock_response.chunks = mock_chunks() # re-create generator
        asyncio.run(stream_chat_response(
            mock_agent, "test", writer=mock_writer, silent=False, verbose=False, verbose_subagents=False
        ))
        
        # Assert subagent thoughts, tool calls, and results are NOT written
        mock_writer.write_thought.assert_not_called()
        mock_writer.write_tool_call.assert_not_called()
        mock_writer.write_tool_result.assert_not_called()

    @patch('antgravity_cli.repl._get_repl_suggestions', return_value=['/exit', '/quit', '/reset'])
    @patch('antgravity_cli.utils.get_workspace_files_and_folders', return_value=[])
    def test_repl_integration_exit_commands(self, mock_files, mock_sugg):
        """Verify that the REPL loop cleanly terminates on /exit or /quit."""
        from antgravity_cli.repl import run_repl
        from antgravity_cli.interfaces import InputReader, OutputWriter
        
        class TestReader(InputReader):
            def __init__(self, inputs):
                self.inputs = inputs
            async def read_input(self, prompt, suggestions=None, file_suggestions=None, subagent_suggestions=None):
                return self.inputs.pop(0)

        class TestWriter(OutputWriter):
            def write_thought(self, text): pass
            def write_text(self, text): pass
            def write_tool_call(self, name, args): pass
            def write_tool_result(self, name, result, error=None): pass

        # 1. Test /exit
        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        reader = TestReader(["/exit"])
        writer = TestWriter()
        
        asyncio.run(run_repl(mock_agent, [], reader, writer))
        # Exited without error

        # 2. Test /quit
        reader = TestReader(["/quit"])
        asyncio.run(run_repl(mock_agent, [], reader, writer))
        # Exited without error

    @patch('antgravity_cli.repl._get_repl_suggestions', return_value=['/exit', '/quit', '/reset'])
    @patch('antgravity_cli.utils.get_workspace_files_and_folders', return_value=[])
    def test_repl_integration_reset_command(self, mock_files, mock_sugg):
        """Verify that the REPL cleans history on /reset."""
        from antgravity_cli.repl import run_repl
        
        class TestReader:
            def __init__(self, inputs):
                self.inputs = inputs
            async def read_input(self, prompt, **kwargs):
                return self.inputs.pop(0)

        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        mock_agent.conversation = MagicMock()
        
        reader = TestReader(["/reset", "/exit"])
        mock_writer = MagicMock()
        
        asyncio.run(run_repl(mock_agent, [], reader, mock_writer))
        mock_agent.conversation.clear_history.assert_called_once()

    @patch('antgravity_cli.repl._get_repl_suggestions', return_value=['/exit'])
    @patch('antgravity_cli.utils.get_workspace_files_and_folders', return_value=[])
    def test_repl_integration_regular_prompt(self, mock_files, mock_sugg):
        """Verify that a regular prompt goes to agent.chat and streams back."""
        from antgravity_cli.repl import run_repl
        from google.antigravity.types import Text
        
        class TestReader:
            def __init__(self, inputs):
                self.inputs = inputs
            async def read_input(self, prompt, **kwargs):
                return self.inputs.pop(0)

        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        mock_agent.conversation = MagicMock()
        
        mock_response = MagicMock()
        async def mock_chunks():
            yield Text(step_index=0, text="Agent response")
            
        mock_response.chunks = mock_chunks()
        
        from unittest.mock import AsyncMock
        mock_agent.chat = AsyncMock(return_value=mock_response)

        reader = TestReader(["Hello Agent", "/exit"])
        mock_writer = MagicMock()
        
        asyncio.run(run_repl(mock_agent, [], reader, mock_writer))
        
        # Verify agent.chat was invoked
        mock_agent.chat.assert_called_once()
        # Verify text was written
        mock_writer.write_text.assert_called_with("Agent response")


if __name__ == '__main__':
    unittest.main()


