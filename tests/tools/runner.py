import subprocess
from typing import List, Tuple
from pathlib import Path
from anvil.core.logging import get_logger

logger = get_logger("tools.runner")

class TestRunner:
    """Runs project tests to verify upgrades."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def run_tests(self) -> Tuple[bool, str]:
        """
        Runs tests and returns (success, output).
        Default: 'pytest' then 'python -m pytest'.
        """
        commands_to_try = [
            ["python3", "-m", "pytest"],
            ["pytest"]
        ]
        
        for cmd in commands_to_try:
            logger.debug(f"Running tests with: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd, 
                    cwd=self.project_root, 
                    capture_output=True, 
                    text=True, 
                    timeout=300 # 5 min timeout
                )
                success = result.returncode == 0
                output = result.stdout + "\n" + result.stderr
                
                if success:
                    logger.info("Tests PASSED ✅")
                else:
                    logger.warning("Tests FAILED ❌")
                    
                return success, output
                
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                logger.debug(f"Test command failed to launch/complete: {e}")
                continue
                
        return False, "Could not launch pytest. Is it installed?"
