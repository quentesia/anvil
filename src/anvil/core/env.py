from pathlib import Path
from importlib import metadata
import sys
import os
import glob
from typing import Optional
from anvil.core.logging import get_logger

logger = get_logger("env.checker")

class EnvironmentChecker:
    """Checks the installed environment for package versions."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.site_packages = self._find_site_packages()
        logger.debug(f"Target site-packages: {self.site_packages}")

    def get_installed_version(self, package_name: str) -> Optional[str]:
        try:
            # If we found a venv, look there by injecting into sys.path
            # This is robust across Python versions where 'path' arg is missing from metadata.distribution
            if self.site_packages:
                original_sys_path = sys.path[:]
                try:
                    sys.path.insert(0, str(self.site_packages))
                    # Force reload of distribution finder if needed, but usually metadata.version checks sys.path dynamically
                    version = metadata.version(package_name)
                finally:
                    sys.path = original_sys_path
            else:
                 version = metadata.version(package_name)
                 
            logger.debug(f"Found installed version for {package_name}: {version}")
            return version
        except metadata.PackageNotFoundError:
            logger.debug(f"Package {package_name} not found in target environment")
            return None
            
    def _find_site_packages(self) -> Optional[Path]:
        """Discovery logic for virtualenvs."""
        # 0. Check active VIRTUAL_ENV (Best for Poetry/Activated Shells)
        env_var = os.environ.get("VIRTUAL_ENV")
        if env_var:
             logger.debug(f"Detected VIRTUAL_ENV: {env_var}")
             return self._scan_venv_lib(Path(env_var))

        # 1. Check for .venv in project root
        if (self.project_root / ".venv").exists():
            return self._scan_venv_lib(self.project_root / ".venv")
            
        # 2. Check for venv
        if (self.project_root / "venv").exists():
            return self._scan_venv_lib(self.project_root / "venv")

        return None

    def _scan_venv_lib(self, venv_path: Path) -> Optional[Path]:
        """Helper to find site-packages inside a venv path."""
        lib = venv_path / "lib"
        if lib.exists():
            # Glob for python version directory (e.g. python3.11)
            py_dirs = list(lib.glob("python*"))
            if py_dirs:
                site = py_dirs[0] / "site-packages"
                if site.exists():
                    return site
        return None
