import subprocess
import shutil
import os
from typing import List, Optional
from pathlib import Path
from anvil.core.logging import get_logger

logger = get_logger("tools.package")

class PackageManager:
    """Abstracts package management operations (pip/uv)."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.has_uv = shutil.which("uv") is not None
        self.has_poetry = shutil.which("poetry") is not None
        self.is_uv_project = (project_root / "uv.lock").exists()
        # Check for poetry configuration
        self.is_poetry_project = (project_root / "poetry.lock").exists()
        if not self.is_poetry_project and (project_root / "pyproject.toml").exists():
            with open(project_root / "pyproject.toml", "r") as f:
                content = f.read()
                if "[tool.poetry]" in content:
                    self.is_poetry_project = True

    def install(self, package: str, version: Optional[str] = None, update_manifest: bool = False) -> bool:
        """
        Installs a specific version of a package.
        :param update_manifest: If True, writes changes to manifest (e.g. 'uv add' or 'poetry add').
                                If False, only installs into environment (e.g. 'uv pip install').
        """
        specifier = f"{package}=={version}" if version else package
        mode = "PERSISTENT" if update_manifest else "TEMPORARY"
        logger.info(f"Installing {specifier} (Mode: {mode})...")
        
        cmd = self._get_install_command(specifier, update_manifest)
        return self._run(cmd)

    # ... (uninstall) ...

    def _get_install_command(self, specifier: str, update_manifest: bool) -> List[str]:
        # PHASE 2: PERSISTENT UPDATE
        if update_manifest:
            # Poetry Priority
            if self.has_poetry and self.is_poetry_project:
                # 'poetry add' updates pyproject.toml and installs
                return ["poetry", "add", specifier]
            
            # UV Priority
            if self.has_uv and (self.is_uv_project or not self.is_poetry_project):
                return ["uv", "add", specifier]

        # PHASE 1: TEMPORARY TRIAL (Env Only)
        if self.has_uv:
            # 'uv pip install' updates venv without touching manifest
            return ["uv", "pip", "install", specifier]
            
        # Standard fallback
        return ["python3", "-m", "pip", "install", specifier]

    def _get_uninstall_command(self, package: str) -> List[str]:
        if self.has_uv and self.is_uv_project:
            return ["uv", "remove", package]
            
        if self.has_uv:
            return ["uv", "pip", "uninstall", package]
            
        return ["python3", "-m", "pip", "uninstall", "-y", package]

    def _run(self, cmd: List[str]) -> bool:
        logger.debug(f"Running command: {' '.join(cmd)}")
        try:
            # Capture output to avoid cluttering TUI, unless debug
            subprocess.check_call(
                cmd, 
                cwd=self.project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stderr:
                 logger.error(f"Stderr: {e.stderr.decode('utf-8', errors='ignore')}")
            return False
