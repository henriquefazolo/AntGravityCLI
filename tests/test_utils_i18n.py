import unittest
from unittest.mock import patch
import os
import sys

from antgravity_cli import i18n, utils


class TestUtilsAndI18n(unittest.TestCase):
    def test_i18n_formatting_warning(self):
        """Verify that i18n.t raises a UserWarning when format arguments are mismatched."""
        with patch('antgravity_cli.i18n._load_translations') as mock_load:
            mock_load.return_value = {"test_key": "Hello {name}"}
            
            with self.assertWarns(UserWarning) as w:
                res = i18n.t("test_module", "test_key", wrong_arg="test")
            
            self.assertEqual(res, "Hello {name}")
            self.assertIn("Format arguments mismatch", str(w.warning))

    def test_utils_get_base_path_frozen(self):
        """Verify that get_base_path returns sys._MEIPASS when running as frozen executable."""
        # 1. Normal execution (unfrozen)
        with patch.object(sys, 'frozen', False, create=True):
            normal_path = utils.get_base_path()
            self.assertEqual(normal_path, os.path.dirname(os.path.abspath(utils.__file__)))
            
        # 2. Standalone frozen execution
        with patch.object(sys, 'frozen', True, create=True), \
             patch.object(sys, '_MEIPASS', "C:\\mock_meipass", create=True):
            frozen_path = utils.get_base_path()
            self.assertEqual(frozen_path, "C:\\mock_meipass")

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
            
            self.assertIn("file1.txt", res)
            self.assertIn("folder1/", res)
            self.assertIn("folder1/file2.txt", res)
            
            self.assertNotIn(".git/", res)
            self.assertNotIn(".git/config", res)
            self.assertNotIn("venv/", res)
            self.assertNotIn("venv/activate", res)
            self.assertNotIn("__pycache__/", res)
            self.assertNotIn("__pycache__/test.pyc", res)

    def test_i18n_translation_keys(self):
        """Verify that i18n translation keys return correct messages for both en-us and pt-br."""
        i18n.set_language("en-us")
        en_msg = i18n.t("repl", "exiting")
        self.assertEqual(en_msg, "Exiting...")
        
        i18n.set_language("pt-br")
        pt_msg = i18n.t("repl", "exiting")
        self.assertEqual(pt_msg, "Saindo...")


if __name__ == '__main__':
    unittest.main()
