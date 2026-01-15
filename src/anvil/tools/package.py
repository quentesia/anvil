import subprocess
import shutil
from typing import List
from pathlib import Path

class PackageManager:
    """Abstracts package management operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.has_uv = shutil.which("uv") is not None
        
    def install(self, package: str) -> bool:
        """Installs a package."""
        cmd = self._get_install_command(package)
        return self._run(cmd)

    def uninstall(self, package: str) -> bool:
        """Uninstalls a package."""
        cmd = self._get_uninstall_command(package)
        return self._run(cmd)
        
    def update(self, package: str) -> bool:
        """Updates a package."""
        # For simplicity, install often handles update
        return self.install(package)

    def _get_install_command(self, package: str) -> List[str]:
        if self.has_uv:
            return ["uv", "pip", "install", package] # or 'uv add' depending on context
        return ["python3", "-m", "pip", "install", package]

    def _get_uninstall_command(self, package: str) -> List[str]:
        if self.has_uv:
            return ["uv", "pip", "uninstall", package]
        return ["python3", "-m", "pip", "uninstall", "-y", package]

    def _run(self, cmd: List[str]) -> bool:
        try:
            subprocess.check_call(cmd, cwd=self.project_root)
            return True
        except subprocess.CalledProcessError:
            return False
