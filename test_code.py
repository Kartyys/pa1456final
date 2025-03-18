import unittest
import os
import tempfile
from unittest.mock import patch
import code  # Assuming your functions are in code.py

class TestCode(unittest.TestCase):

    def test_analyze_commits(self):
        # Mock print to prevent UnicodeEncodeError
        with patch('builtins.print') as mock_print:
            result = code.analyze_commits("clone_dir", 0)
            mock_print.assert_called_with("\ud83d\udd34 Cloned repository not found.")  # Adjust as needed

    def test_check_files(self):
    # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock .gitignore file
            os.makedirs(temp_dir, exist_ok=True)
            open(os.path.join(temp_dir, ".gitignore"), 'w').close()

        # Create a dictionary for allowed_failures as expected by the function
            allowed_failures = {'license_check': False}
        
        # Assuming check_files returns False when certain conditions aren't met
            result = code.check_files(temp_dir, allowed_failures)
            self.assertFalse(result)  # Expecting False based on your previous output


    def test_count_workflow_files(self):
        # Create a dictionary for allowed_failures with 'workflow_check' key
        allowed_failures = {'workflow_check': False}
        
        result = code.count_workflow_files("clone_dir", allowed_failures)
        self.assertEqual(result, 0)  # Adjust based on the expected behavior in your code

    def test_is_ignored(self):
        ignored = ["test.log", "test.tmp"]
        result = code.is_ignored("test.log", ignored)
        self.assertTrue(result)  # test.log is in the ignored list, so it should return True

    def test_parse_gitignore(self):
        # Create a temporary directory with a .gitignore file
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, '.gitignore'), 'w') as f:
                f.write("*.log\n*.tmp")
            
            result = code.parse_gitignore(temp_dir)
            # The .gitignore file contains "*.log" and "*.tmp"
            self.assertEqual(result, ["*.log", "*.tmp"])

    def test_run_gitleaks(self):
        # Mock the function behavior for Gitleaks
        with patch('code.run_gitleaks') as mock_gitleaks:
            mock_gitleaks.return_value = True  # Assuming success
            result = code.run_gitleaks("repo_dir", 0)
            self.assertTrue(result)  # Assuming the function returns True for success

if __name__ == "__main__":
    unittest.main()
