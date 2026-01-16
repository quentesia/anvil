from pathlib import Path
from importlib import metadata
from typing import Optional
from anvil.core.logging import get_logger

logger = get_logger("env.checker")

class EnvironmentChecker:
    """Checks the installed environment for package versions."""
    
    def __init__(self, project_root: str):
        # In a real scenario, we might need to inspect the venv at project_root
        # effectively, not just the running process.
        # But for 'python -m anvil.main', we are running FROM the venv.
        self.project_root = Path(project_root)

    def get_installed_version(self, package_name: str) -> Optional[str]:
        try:
            version = metadata.version(package_name)
            logger.debug(f"Found installed version for {package_name}: {version}")
            return version
        except metadata.PackageNotFoundError:
            logger.debug(f"Package {package_name} not found in current environment")
            return None
