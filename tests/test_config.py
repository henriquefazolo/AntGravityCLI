import unittest
from unittest.mock import patch, MagicMock
import os

from antgravity_cli.config import setup_agent_config
from antgravity_cli.handlers import cli_ask_user_handler


class TestAntigravityConfig(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Verify that the correct error is displayed when the API Key is missing."""
        with self.assertRaises(ValueError) as ctx:
            setup_agent_config(
                model="gemini-3.1-flash-lite",
                yolo=False,
                workspace=["."],
                system_instruction=None,
                api_key="",
                skills_path=[]
            )
        self.assertIn("Gemini API key not found", str(ctx.exception))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    def test_setup_agent_config_skills_fallback(self):
        """Verify that setup_agent_config resolves both custom -k paths and the native CLI installation folder's builtin/skills."""
        dummy_path = os.path.abspath(os.path.normpath("some/other/path"))
        config = setup_agent_config(
            model="gemini-3.5-flash",
            yolo=False,
            workspace=["."],
            system_instruction=None,
            api_key=None,
            skills_path=[dummy_path]
        )
        self.assertIsNotNone(config.skills_paths)
        self.assertEqual(len(config.skills_paths), 2)
        self.assertIn(dummy_path, config.skills_paths)
        self.assertTrue(config.skills_paths[1].endswith(os.path.join("builtin", "skills")))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    def test_setup_agent_config_skills_normalization(self):
        """Verify that setup_agent_config normalizes skills paths to absolute paths and deduplicates them."""
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

    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
    @patch('antgravity_cli.config.os.path.isdir')
    @patch('antgravity_cli.subagents.discover_subagents_in_paths')
    def test_setup_agent_config_subagents(self, mock_discover, mock_isdir):
        """Verify that setup_agent_config resolves and injects discovered subagents."""
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


if __name__ == '__main__':
    unittest.main()
