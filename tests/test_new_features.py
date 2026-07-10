import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import asyncio
from colorama import Fore, Style
from google.antigravity.types import Step, StepType, StepSource, StepTarget, ToolCall, SubagentConfig

from antgravity_cli.utils import parse_yaml_frontmatter, get_workspace_files_and_folders
from antgravity_cli.parser.preprocessor import PromptPreprocessor, preprocess_prompt
from antgravity_cli.builtin.commands.reload import ReloadCommand
from antgravity_cli.builtin.commands.clear import ClearCommand
from antgravity_cli.builtin.commands.history import HistoryCommand
from antgravity_cli.builtin.commands.save import SaveCommand
from antgravity_cli.builtin.commands.load import LoadCommand
from antgravity_cli.builtin.commands.config import ConfigCommand
from antgravity_cli.builtin.commands import get_command_map, get_command_triggers
from antgravity_cli.console_io.reader import ConsoleInputReader


class TestNewFeatures(unittest.TestCase):

    def test_parse_yaml_frontmatter(self):
        """Test parse_yaml_frontmatter splits YAML frontmatter from body correctly."""
        content = "---\nname: my_skill\ndescription: A test skill\n---\n# My Skill Body\nInstructions here."
        meta, body = parse_yaml_frontmatter(content)
        self.assertEqual(meta.get("name"), "my_skill")
        self.assertEqual(meta.get("description"), "A test skill")
        self.assertEqual(body, "# My Skill Body\nInstructions here.")

        # Test content without frontmatter
        meta2, body2 = parse_yaml_frontmatter("Hello World")
        self.assertEqual(meta2, {})
        self.assertEqual(body2, "Hello World")

    def test_preprocessor_singleton(self):
        """Test PromptPreprocessor singleton delegates correctly and is stateless."""
        from antgravity_cli.parser.preprocessor import _preprocessor
        self.assertIsInstance(_preprocessor, PromptPreprocessor)
        
        # Test wrapper
        prompt = "Hello /skill_name"
        with patch.object(_preprocessor, 'preprocess', return_value="processed") as mock_preprocess:
            res = preprocess_prompt(prompt)
            mock_preprocess.assert_called_once_with(prompt, None, disabled_skills=None)
            self.assertEqual(res, "processed")

    @patch('antgravity_cli.builtin.commands.reload.click.echo')
    def test_reload_command(self, mock_echo):
        """Test reload command invalidates cache and triggers rediscovery."""
        cmd = ReloadCommand()
        self.assertEqual(cmd.triggers, ["/reload"])
        self.assertEqual(cmd.description_key, "command_reload_desc")

        mock_agent = MagicMock()
        mock_ws_context = MagicMock()
        mock_ws_context.discover_skills.return_value = ["skill1"]
        mock_ws_context.discover_subagents.return_value = [SubagentConfig(name="MockSub", description="Desc")]
        mock_agent.config._ws_context = mock_ws_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(cmd.execute(mock_agent))
            self.assertTrue(res)
            mock_ws_context.invalidate_cache.assert_called_once()
            mock_ws_context.discover_subagents.assert_called_once_with(force_refresh=True)
            mock_ws_context.discover_skills.assert_called_once_with(force_refresh=True)
        finally:
            loop.close()

    @patch('antgravity_cli.builtin.commands.clear.os.system')
    def test_clear_command(self, mock_system):
        """Test clear command issues system clear command."""
        cmd = ClearCommand()
        self.assertEqual(cmd.triggers, ["/clear", "/cls"])
        self.assertEqual(cmd.description_key, "command_clear_desc")

        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(cmd.execute(MagicMock()))
            self.assertTrue(res)
            mock_system.assert_called_once()
        finally:
            loop.close()

    @patch('antgravity_cli.builtin.commands.history.get_history_file_path')
    @patch('antgravity_cli.builtin.commands.history.click.echo')
    @patch('os.path.isfile')
    def test_history_command(self, mock_isfile, mock_echo, mock_history_path):
        """Test history command reads and prints the requested number of prompt history entries."""
        mock_history_path.return_value = "fake_history.txt"
        mock_isfile.return_value = True
        
        cmd = HistoryCommand()
        self.assertEqual(cmd.triggers, ["/history"])
        self.assertEqual(cmd.description_key, "command_history_desc")

        history_file_content = "+hello\n+world\n+summarize file\n"
        loop = asyncio.new_event_loop()
        try:
            with patch('builtins.open', mock_open(read_data=history_file_content)):
                res = loop.run_until_complete(cmd.execute(MagicMock(), context=" 2"))
                self.assertTrue(res)
                # Verify mock_echo calls including color codes and formatting spaces
                mock_echo.assert_any_call(f"  {Fore.CYAN}2   {Style.RESET_ALL} world")
                mock_echo.assert_any_call(f"  {Fore.CYAN}3   {Style.RESET_ALL} summarize file")
        finally:
            loop.close()

    @patch('antgravity_cli.builtin.commands.save.get_history_file_path')
    @patch('antgravity_cli.builtin.commands.save.click.echo')
    @patch('antgravity_cli.builtin.commands.save.i18n.t')
    def test_save_command(self, mock_i18n_t, mock_echo, mock_history_path):
        """Test save command serialization and file write."""
        mock_i18n_t.return_value = "Session saved successfully"
        from google.antigravity.types import StepType
        mock_history_path.return_value = "fake_history_dir/history"
        cmd = SaveCommand()
        self.assertEqual(cmd.triggers, ["/save"])
        
        mock_agent = MagicMock()
        step = Step(
            id="1",
            step_index=0,
            type=StepType.TEXT_RESPONSE,
            source=StepSource.MODEL,
            target=StepTarget.USER
        )
        mock_agent.conversation.history = [step]

        loop = asyncio.new_event_loop()
        try:
            with patch('os.makedirs'), patch('builtins.open', mock_open()) as m_open:
                res = loop.run_until_complete(cmd.execute(mock_agent, context="my_session"))
                self.assertTrue(res)
                m_open.assert_called_once()
                self.assertIn("my_session.json", m_open.call_args[0][0])
        finally:
            loop.close()

    @patch('antgravity_cli.builtin.commands.load.get_history_file_path')
    @patch('antgravity_cli.builtin.commands.load.click.echo')
    @patch('antgravity_cli.builtin.commands.load.i18n.t')
    @patch('os.path.isfile')
    def test_load_command(self, mock_isfile, mock_i18n_t, mock_echo, mock_history_path):
        """Test load command validation and restoration of steps."""
        mock_i18n_t.return_value = "Session loaded successfully"
        mock_history_path.return_value = "fake_history_dir/history"
        mock_isfile.return_value = True

        cmd = LoadCommand()
        self.assertEqual(cmd.triggers, ["/load"])

        step_data = {
            "id": "1",
            "step_index": 0,
            "type": "TEXT_RESPONSE",
            "source": "MODEL",
            "target": "TARGET_USER"
        }
        session_content = json.dumps([step_data])

        mock_agent = MagicMock()
        mock_agent.conversation.history = []
        
        loop = asyncio.new_event_loop()
        try:
            with patch('builtins.open', mock_open(read_data=session_content)):
                res = loop.run_until_complete(cmd.execute(mock_agent, context="my_session"))
                self.assertTrue(res)
                self.assertEqual(len(mock_agent.conversation.history), 1)
                self.assertIsInstance(mock_agent.conversation.history[0], Step)
                self.assertEqual(mock_agent.conversation.history[0].id, "1")
        finally:
            loop.close()

    @patch('antgravity_cli.builtin.commands.config.click.echo')
    def test_config_command(self, mock_echo):
        """Test config command prints workspaces, skills paths, and masks API key."""
        cmd = ConfigCommand()
        self.assertEqual(cmd.triggers, ["/config"])

        mock_agent = MagicMock()
        mock_agent.config.model = "gemini-test-model"
        mock_agent.config.api_key = "AIzaSyTestApiKeyString123"
        mock_agent.config.workspaces = ["/workspace1"]
        mock_agent.config.skills_paths = ["/skills1"]

        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(cmd.execute(mock_agent))
            self.assertTrue(res)
            # Mask API key verify
            mock_echo.assert_any_call("  \x1b[36mAPI Key:\x1b[0m      AIzaSy...g123")
        finally:
            loop.close()

    @patch('sys.stdin.isatty')
    @patch('antgravity_cli.runner.setup_agent_config')
    @patch('antgravity_cli.runner.preprocess_prompt')
    @patch('antgravity_cli.runner.stream_chat_response')
    @patch('antgravity_cli.runner.Agent')
    def test_runner_stdin_pipe(self, mock_agent_class, mock_stream, mock_preprocess, mock_config, mock_isatty):
        """Test that runner detects piped stdin input when sys.stdin is not a tty."""
        mock_isatty.return_value = False
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value.__aenter__.return_value = mock_agent_instance
        from antgravity_cli.runner import run_cli
        
        loop = asyncio.new_event_loop()
        try:
            with patch('sys.stdin.read', return_value="piped hello"):
                loop.run_until_complete(run_cli(
                    prompt=None,
                    model="model",
                    yolo=False,
                    workspace=None,
                    system_instruction=None,
                    api_key="AIzaSyKey",
                    skills_path=None
                ))
                # Verify preprocess was called with the piped prompt
                mock_preprocess.assert_called_once_with("piped hello", mock_config.return_value.skills_paths)
        finally:
            loop.close()

    @patch('antgravity_cli.console_io.reader.input')
    def test_multiline_input_reader(self, mock_input):
        """Test ConsoleInputReader loops when prompt lines end with a backslash."""
        # Simulated lines: first ends with \, second is normal
        mock_input.side_effect = ["first line \\", "second line"]
        
        reader = ConsoleInputReader()
        loop = asyncio.new_event_loop()
        try:
            user_input = loop.run_until_complete(reader.read_input("prompt"))
            self.assertEqual(user_input, "first line\nsecond line")
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
