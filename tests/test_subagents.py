import unittest
import os
import tempfile
import shutil

from antgravity_cli.subagents import parse_agent_md, discover_subagents_in_paths


class TestAntigravitySubagents(unittest.TestCase):
    def test_parse_agent_md_full(self):
        """Verify that parse_agent_md correctly parses YAML frontmatter and body."""
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


if __name__ == '__main__':
    unittest.main()
