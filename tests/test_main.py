import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import os
import sys

from antgravity_cli.main import main
from antgravity_cli.config import setup_agent_config
from antgravity_cli.console_io import ConsoleOutputWriter


class TestAntigravityMain(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_help_flag(self):
        """Verify that the help command is displayed correctly."""
        result = self.runner.invoke(main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Usage:', result.output)
        self.assertIn('--model', result.output)
        self.assertIn('--yolo', result.output)
        self.assertIn('--workspace', result.output)

    @patch('antgravity_cli.runner.Agent')
    @patch('antgravity_cli.config.LocalAgentConfig')
    @patch('antgravity_cli.runner.stream_chat_response')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake_test_key'})
    def test_cli_runs_with_prompt(self, mock_stream, mock_config, mock_agent):
        """Verify that the basic prompt execution flow works and invokes the correct agents."""
        mock_agent_instance = MagicMock()
        mock_agent.return_value.__aenter__.return_value = mock_agent_instance
        
        result = self.runner.invoke(main, ['Oi'])
        self.assertEqual(result.exit_code, 0)
        
        mock_config.assert_called_once()
        mock_agent.assert_called_once_with(mock_config.return_value)
        
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
        
        args, kwargs = mock_stream.call_args
        self.assertEqual(args[0], mock_agent_instance)
        self.assertEqual(args[1], 'Oi')
        self.assertIsInstance(args[2], ConsoleOutputWriter)
        self.assertEqual(kwargs.get('silent'), True)

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
        
        mock_run_cli.assert_called_once()
        args, kwargs = mock_run_cli.call_args
        self.assertEqual(args[0], None)  # prompt
        self.assertEqual(args[1], 'gemini-custom')  # model
        self.assertEqual(args[2], True)  # yolo
        self.assertEqual(args[5], 'envvar-api-key')  # api_key
        self.assertEqual(kwargs.get('language'), 'pt-br')  # language

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
        self.assertEqual(args[0], None)  # prompt
        self.assertEqual(args[1], 'gemini-custom')  # model
        self.assertEqual(args[2], True)  # yolo
        self.assertEqual(args[3], (os.path.abspath("."),))  # workspace
        self.assertEqual(args[4], 'custom-instruction')  # system_instruction
        self.assertEqual(args[5], 'envvar-api-key')  # api_key
        self.assertEqual(args[6], (os.path.abspath("."),))  # skills_path
        self.assertEqual(kwargs.get('silent'), True)
        self.assertEqual(kwargs.get('verbose'), True)
        self.assertEqual(kwargs.get('verbose_subagents'), True)
        self.assertEqual(kwargs.get('language'), 'pt-br')

    @patch('dotenv.load_dotenv')
    @patch('os.path.exists')
    @patch('antgravity_cli.utils.get_base_path')
    def test_env_loading_precedence(self, mock_get_base_path, mock_exists, mock_load_dotenv):
        """Verify that .env files are loaded from the base installation and CWD with correct overrides."""
        import importlib
        import antgravity_cli.main as main_module

        mock_get_base_path.return_value = "C:\\base_dir"
        mock_exists.side_effect = lambda path: path.endswith('.env')
        
        importlib.reload(main_module)
        
        self.assertEqual(mock_load_dotenv.call_count, 2)
        calls = mock_load_dotenv.call_args_list
        self.assertEqual(calls[0][0][0], os.path.join("C:\\base_dir", ".env"))
        self.assertEqual(calls[1][0][0], os.path.abspath(".env"))
        self.assertEqual(calls[1][1].get('override'), True)

    @patch('dotenv.load_dotenv')
    @patch('os.path.exists')
    @patch('sys.argv', ['antgravity_cli/main.py', '-e', 'custom_env_file.env'])
    def test_env_loading_custom_file(self, mock_exists, mock_load_dotenv):
        """Verify that passing -e loads only the custom env file and overrides standard envs."""
        import importlib
        import antgravity_cli.main as main_module

        mock_exists.side_effect = lambda path: True if path == 'custom_env_file.env' else False
        
        importlib.reload(main_module)
        mock_load_dotenv.assert_called_once_with('custom_env_file.env', override=True)

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
            "Gemini API Key (deixe em branco para pular)": "test_api_key",
            "Gemini Model": "gemini-3.1-flash-lite",
            "Modelo Gemini": "gemini-3.1-flash-lite",
            "Language (en-us, pt-br)": "pt-br",
            "Idioma (en-us, pt-br)": "pt-br"
        }.get(text, "default_val")
        mock_confirm.return_value = True
        
        tmp_dir = tempfile.mkdtemp()
        orig_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            run_init()
            
            self.assertTrue(os.path.isdir(".agents"))
            self.assertTrue(os.path.isdir(os.path.join(".agents", "skills")))
            self.assertTrue(os.path.isdir(os.path.join(".agents", "subagents")))
            self.assertTrue(os.path.isfile(os.path.join(".agents", "AGENTS.md")))
            self.assertTrue(os.path.isfile(os.path.join(".agents", "skills", "skill_example", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(".agents", "subagents", "subagent_example", "AGENT.md")))
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

    @patch('antgravity_cli.main.run_cli')
    def test_run_command_success(self, mock_run_cli):
        """Verify that 'run' executes correctly with a valid UTF-8 script file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write("Hello agent")
            temp_name = f.name
        try:
            result = self.runner.invoke(main, ['run', temp_name])
            self.assertEqual(result.exit_code, 0)
            mock_run_cli.assert_called_once()
            args, kwargs = mock_run_cli.call_args
            self.assertEqual(args[0], "Hello agent")
        finally:
            os.remove(temp_name)

    def test_run_command_file_not_found(self):
        """Verify that 'run' displays an error message when the file does not exist."""
        result = self.runner.invoke(main, ['run', 'non_existent_file_path.txt'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("does not exist", result.output)

    @patch('antgravity_cli.main.run_cli')
    def test_run_command_latin1_fallback(self, mock_run_cli):
        """Verify that 'run' warns and falls back to latin-1 for non-UTF-8 files."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Ol\xe1 agente")
            temp_name = f.name
        try:
            result = self.runner.invoke(main, ['run', temp_name])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Warning: Failed to decode", result.output)
            mock_run_cli.assert_called_once()
            args, _ = mock_run_cli.call_args
            self.assertEqual(args[0], "Olá agente")
        finally:
            os.remove(temp_name)


if __name__ == '__main__':
    unittest.main()
