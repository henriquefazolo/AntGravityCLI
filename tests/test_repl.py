import unittest
from unittest.mock import patch, MagicMock
import asyncio
import os
import tempfile
import shutil
from colorama import Fore, Style
from prompt_toolkit.document import Document

from antgravity_cli.repl import run_repl, stream_chat_response, _get_repl_suggestions, get_active_subagent_name
from antgravity_cli.interfaces import InputReader, OutputWriter
from antgravity_cli.console_io import ConsoleOutputWriter, ConsoleInputReader, AntCompleter, CommandCompleter, _PATTERN_CMD
from antgravity_cli import i18n
from google.antigravity.types import Thought, Text, ToolCall, ToolResult


class DummyStep:
    def __init__(self, step_index, trajectory_id):
        self.step_index = step_index
        self.trajectory_id = trajectory_id
        self.tool_calls = []


class TestAntigravityREPL(unittest.TestCase):
    def setUp(self):
        i18n.set_language("en-us")

    @patch('antgravity_cli.repl.click.echo')
    def test_run_repl_exit_command(self, mock_echo):
        """Verify that the REPL exits and prints 'Exiting...' upon receiving /quit."""
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
                return "/quit"
                
        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        mock_echo.assert_called_with(f"{Fore.YELLOW}Exiting...{Style.RESET_ALL}")

    @patch('antgravity_cli.repl.click.echo')
    @patch('antgravity_cli.repl._get_repl_suggestions')
    def test_run_repl_displays_skills_limit(self, mock_get_repl_suggestions, mock_echo):
        """Verify that the welcome banner prints local skills in compact format when there are more than 5."""
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
                return "/quit"
                
        # Scenario 1: More than 5 skills (should show compact banner)
        mock_get_repl_suggestions.return_value = ["/exit", "/quit", "/reset", "/s1", "/s2", "/s3", "/s4", "/s5", "/s6", "/s7"]
        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        
        i18n.set_language("en-us")
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        any_match_compact_en = any("  7 skills active | /help for details" == args[0] for args, _ in mock_echo.call_args_list)
        self.assertTrue(any_match_compact_en)

        # Scenario 2: Portuguese switches correctly
        mock_echo.reset_mock()
        i18n.set_language("pt-br")
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        any_match_compact_pt = any("  7 skills ativas | /help para detalhes" == args[0] for args, _ in mock_echo.call_args_list)
        self.assertTrue(any_match_compact_pt)

    @patch('antgravity_cli.repl.click.echo')
    @patch('antgravity_cli.repl._get_repl_suggestions')
    def test_run_repl_displays_ant_art_logo(self, mock_get_repl_suggestions, mock_echo):
        """Verify that the welcome banner prints the Option 1 ant logo correctly."""
        class MockInputReader(InputReader):
            async def read_input(self, prompt_text: str, suggestions=None, *args, **kwargs) -> str:
                return "/quit"
                
        mock_get_repl_suggestions.return_value = ["/exit", "/quit", "/reset"]
        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        
        asyncio.run(run_repl(mock_agent, [], reader=MockInputReader()))
        
        logo_line_1 = f"  {Fore.CYAN}▄▀▀▄       ▄▀▀▄{Style.RESET_ALL}"
        logo_line_2 = f"   {Fore.CYAN}▀▄ ▀▄   ▄▀ ▄▀{Style.RESET_ALL}"
        logo_line_3 = f"    {Fore.BLUE}▄█████████▄{Style.RESET_ALL}"
        
        self.assertTrue(any(logo_line_1 == args[0] for args, _ in mock_echo.call_args_list))
        self.assertTrue(any(logo_line_2 == args[0] for args, _ in mock_echo.call_args_list))
        self.assertTrue(any(logo_line_3 == args[0] for args, _ in mock_echo.call_args_list))

    def test_get_repl_suggestions_fallback(self):
        """Verify that _get_repl_suggestions falls back to default folders if paths are empty or None."""
        suggestions_none = _get_repl_suggestions(None)
        self.assertIn("/generate_skill_template", suggestions_none)
        self.assertIn("/exit", suggestions_none)
        self.assertIn("/reset", suggestions_none)
        
        suggestions_empty = _get_repl_suggestions([])
        self.assertIn("/generate_skill_template", suggestions_empty)

    def test_suggestions_exclude_templates(self):
        """Verify that skill_example and subagent_example are excluded from autocompletion."""
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

    def test_command_completer_pattern_backspace_and_filtering(self):
        """Verify that CommandCompleter with _PATTERN_CMD handles backspaces, spaces, and filters commands properly."""
        completer = CommandCompleter(["/exit", "/quit", "/reset", "/generate_skill_template", "/gerund"], ignore_case=True, pattern=_PATTERN_CMD)
        
        doc1 = Document("/gener")
        completions1 = list(completer.get_completions(doc1, None))
        self.assertEqual(len(completions1), 1)
        self.assertEqual(completions1[0].text, "/generate_skill_template")
        
        doc2 = Document("/gene")
        completions2 = list(completer.get_completions(doc2, None))
        self.assertEqual(len(completions2), 1)
        self.assertEqual(completions2[0].text, "/generate_skill_template")
        
        doc3 = Document("/ge")
        completions3 = list(completer.get_completions(doc3, None))
        self.assertEqual(len(completions3), 2)
        self.assertIn("/generate_skill_template", [c.text for c in completions3])
        self.assertIn("/gerund", [c.text for c in completions3])
        
        doc4 = Document("generate")
        completions4 = list(completer.get_completions(doc4, None))
        self.assertEqual(len(completions4), 0)

        doc5 = Document("Olá ")
        completions5 = list(completer.get_completions(doc5, None))
        self.assertEqual(len(completions5), 0)

    def test_ant_completer(self):
        """Verify that AntCompleter handles slash commands, at-sign file completions, and colon subagent completions correctly."""
        completer = AntCompleter(
            command_suggestions=["/exit", "/generate_skill_template"],
            file_suggestions=["README.md", "antgravity_cli/main.py"],
            subagent_suggestions=["test_helper", "log_analyzer"]
        )
        
        doc1 = Document("/ex")
        completions1 = list(completer.get_completions(doc1, None))
        self.assertEqual(len(completions1), 1)
        self.assertEqual(completions1[0].text, "/exit")
        
        doc2 = Document("@REA")
        completions2 = list(completer.get_completions(doc2, None))
        self.assertEqual(len(completions2), 1)
        self.assertEqual(completions2[0].text, "@README.md")
        
        doc3 = Document("@")
        completions3 = list(completer.get_completions(doc3, None))
        self.assertEqual(len(completions3), 2)
        texts = [c.text for c in completions3]
        self.assertIn("@README.md", texts)
        self.assertIn("@antgravity_cli/main.py", texts)

        # Test subagent completion
        doc4 = Document(":tes")
        completions4 = list(completer.get_completions(doc4, None))
        self.assertEqual(len(completions4), 1)
        self.assertEqual(completions4[0].text, ":test_helper")
        
        doc5 = Document(":")
        completions5 = list(completer.get_completions(doc5, None))
        self.assertEqual(len(completions5), 2)
        subagent_texts = [c.text for c in completions5]
        self.assertIn(":test_helper", subagent_texts)
        self.assertIn(":log_analyzer", subagent_texts)

    def test_get_active_subagent_name(self):
        """Verify that get_active_subagent_name extracts the subagent name from history."""
        from google.antigravity import types
        
        mock_agent = MagicMock()
        mock_agent.conversation.history = []
        self.assertIsNone(get_active_subagent_name(mock_agent))
        
        step1 = types.Step(
            id="1",
            step_index=0,
            type=types.StepType.TOOL_CALL,
            source=types.StepSource.MODEL,
            target=types.StepTarget.USER
        )
        mock_agent.conversation.history = [step1]
        self.assertIsNone(get_active_subagent_name(mock_agent))
        
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

    @patch('antgravity_cli.repl.ConsoleOutputWriter')
    def test_stream_chat_response_verbose_subagents(self, mock_writer_class):
        """Verify that stream_chat_response formats subagent chunks under verbose_subagents."""
        mock_writer = mock_writer_class.return_value
        mock_agent = MagicMock()
        
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
        
        mock_writer.reset_mock()
        asyncio.run(stream_chat_response(
            mock_agent, "test", writer=mock_writer, silent=False, verbose=False, verbose_subagents=True
        ))
        
        mock_writer.write_thought.assert_called_once_with("[TestSubagent] Subagent logic thoughts")
        mock_writer.write_tool_call.assert_called_once_with("[TestSubagent] read_file", {"path": "a.txt"})
        mock_writer.write_tool_result.assert_called_once_with("[TestSubagent] read_file", "content", None)
        
        mock_writer.reset_mock()
        mock_response.chunks = mock_chunks()
        asyncio.run(stream_chat_response(
            mock_agent, "test", writer=mock_writer, silent=False, verbose=False, verbose_subagents=False
        ))
        
        mock_writer.write_thought.assert_not_called()
        mock_writer.write_tool_call.assert_not_called()
        mock_writer.write_tool_result.assert_not_called()

    @patch('antgravity_cli.repl._get_repl_suggestions', return_value=['/exit', '/quit', '/reset'])
    @patch('antgravity_cli.utils.get_workspace_files_and_folders', return_value=[])
    def test_repl_integration_exit_commands(self, mock_files, mock_sugg):
        """Verify that the REPL loop cleanly terminates on /exit or /quit."""
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

        mock_agent = MagicMock()
        mock_agent.config = MagicMock()
        mock_agent.config.workspaces = ["."]
        reader = TestReader(["/exit"])
        writer = TestWriter()
        
        asyncio.run(run_repl(mock_agent, [], reader, writer))

        reader = TestReader(["/quit"])
        asyncio.run(run_repl(mock_agent, [], reader, writer))

    @patch('antgravity_cli.repl._get_repl_suggestions', return_value=['/exit', '/quit', '/reset'])
    @patch('antgravity_cli.utils.get_workspace_files_and_folders', return_value=[])
    def test_repl_integration_reset_command(self, mock_files, mock_sugg):
        """Verify that the REPL cleans history on /reset."""
        class TestReader(InputReader):
            def __init__(self, inputs):
                self.inputs = inputs
            async def read_input(self, prompt, suggestions=None, file_suggestions=None, subagent_suggestions=None):
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
        class TestReader(InputReader):
            def __init__(self, inputs):
                self.inputs = inputs
            async def read_input(self, prompt, suggestions=None, file_suggestions=None, subagent_suggestions=None):
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
        mock_agent.chat.assert_called_once()
        mock_writer.write_text.assert_called_with("Agent response")


if __name__ == '__main__':
    unittest.main()
