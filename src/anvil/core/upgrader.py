from pathlib import Path
from typing import List
from anvil.core.models import Dependency, UpdateProposal
from anvil.core.parsers.requirements import RequirementsParser
from anvil.core.parsers.pyproject import PyProjectParser
from anvil.tools.package import PackageManager
from anvil.tools.runner import TestRunner
from anvil.retrievers.main import ChangelogRetriever
from anvil.core.logging import get_logger

logger = get_logger("upgrader")

class Upgrader:
    """Orchestrates the upgrade process."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        logger.debug(f"Initialized Upgrader for path: {self.project_root}")
        self.package_manager = PackageManager(self.project_root)
        self.test_runner = TestRunner(self.project_root)
        self.retriever = ChangelogRetriever()
        
    def scan_dependencies(self) -> List[Dependency]:
        """Scans for dependencies in known files."""
        deps = []
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            logger.debug(f"Found requirements.txt, parsing...")
            deps.extend(RequirementsParser(req_file).parse())
            
        # Check pyproject.toml
        pyproj_file = self.project_root / "pyproject.toml"
        if pyproj_file.exists():
             logger.debug(f"Found pyproject.toml, parsing...")
             deps.extend(PyProjectParser(pyproj_file).parse())
             
        logger.info(f"Scan complete. Found {len(deps)} total dependencies.")
        return deps
        
    def check_updates(self, dry_run: bool = True):
        """
        Main entry point to check and apply updates.
        1. Scan
        2. Analyze (Agent) - Placeholder for now
        3. Report / Apply
        """
        logger.info("Starting dependency check...")
        deps = self.scan_dependencies()
        
        for dep in deps:
            logger.debug(f"Processing dependency: {dep.name} ({dep.current_version or 'unknown version'})")
            
            source_url = self.retriever.get_source_url(dep.name)
            if source_url:
                logger.info(f" - {dep.name}: Source URL found -> {source_url}")
            else:
                logger.debug(f" - {dep.name}: Source URL not found")
