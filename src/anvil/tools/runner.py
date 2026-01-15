import subprocess
from typing import List, Tuple
from pathlib import Path

class TestRunner:
    """Runs project tests to verify upgrades."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def run_tests(self) -> Tuple[bool, str]:
        """
        Runs tests and returns (success, output).
        Currently defaults to pytest.
        """
        # TODO: Detect test runner (pytest, unittest, nose, etc.)
        cmd = ["pytest"]
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.project_root, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.returncode == 0, result.stdout + result.stderr
        except FileNotFoundError:
            return False, "pytest not found"
