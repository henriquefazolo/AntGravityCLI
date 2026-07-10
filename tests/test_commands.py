import unittest
from unittest.mock import patch, MagicMock
import asyncio
from colorama import Fore, Style

from antgravity_cli.builtin.commands import get_command_map, get_command_triggers
from antgravity_cli.builtin.commands.help import HelpCommand
from antgravity_cli.builtin.commands.ants import AntsCommand
from antgravity_cli.builtin.commands.exit import ExitCommand
from antgravity_cli.builtin.commands.reset import ResetCommand
from antgravity_cli.builtin.commands.disable_skill import DisableSkillCommand
from antgravity_cli.builtin.commands.enable_skill import EnableSkillCommand
from antgravity_cli.builtin.commands.disable_agent import DisableAgentCommand
from antgravity_cli.builtin.commands.enable_agent import EnableAgentCommand


class TestAntigravityCommands(unittest.TestCase):
    def test_command_handlers_registry(self):
        """Verify that commands registry correctly returns maps and triggers."""
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
        self.assertIn("/reload", cmd_map)
        self.assertIn("/clear", cmd_map)
        self.assertIn("/cls", cmd_map)
        self.assertIn("/history", cmd_map)
        self.assertIn("/save", cmd_map)
        self.assertIn("/load", cmd_map)
        self.assertIn("/config", cmd_map)
        
        triggers = get_command_triggers()
        self.assertEqual(triggers, [
            "/ants",
            "/clear",
            "/cls",
            "/config",
            "/disable_agent",
            "/disable_skill",
            "/enable_agent",
            "/enable_skill",
            "/exit",
            "/help",
            "/history",
            "/load",
            "/quit",
            "/reload",
            "/reset",
            "/save",
            "/subagents",
            "?"
        ])

    @patch('antgravity_cli.builtin.commands.help.click.echo')
    def test_help_command_handler(self, mock_echo):
        """Verify that HelpCommand displays commands, skills, and subagents, and returns True."""
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
        cmd = ExitCommand()
        self.assertEqual(cmd.description_key, "command_exit_desc")
        
        result = asyncio.run(cmd.execute(MagicMock()))
        self.assertFalse(result)
        mock_echo.assert_called_once()

    @patch('antgravity_cli.builtin.commands.reset.click.echo')
    def test_reset_command_handler(self, mock_echo):
        """Verify that ResetCommand clears history and returns True."""
        cmd = ResetCommand()
        self.assertEqual(cmd.description_key, "command_reset_desc")
        
        mock_agent = MagicMock()
        result = asyncio.run(cmd.execute(mock_agent))
        self.assertTrue(result)
        mock_agent.conversation.clear_history.assert_called_once()
        mock_echo.assert_called_once()

    @patch('antgravity_cli.builtin.commands.disable_skill.click.echo')
    def test_disable_enable_skill_command(self, mock_echo):
        """Verify that DisableSkillCommand and EnableSkillCommand update agent._disabled_skills."""
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


if __name__ == '__main__':
    unittest.main()
