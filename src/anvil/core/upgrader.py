from pathlib import Path
from typing import List
from anvil.core.models import Dependency, UpdateProposal
from anvil.core.parsers.requirements import RequirementsParser
from anvil.core.parsers.pyproject import PyProjectParser
from anvil.tools.package import PackageManager
from anvil.tools.runner import TestRunner
# from anvil.agent.graph import builder as graph_builder # Validation pending

class Upgrader:
    """Orchestrates the upgrade process."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.package_manager = PackageManager(self.project_root)
        self.test_runner = TestRunner(self.project_root)
        
    def scan_dependencies(self) -> List[Dependency]:
        """Scans for dependencies in known files."""
        deps = []
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            deps.extend(RequirementsParser(req_file).parse())
            
        # Check pyproject.toml
        pyproj_file = self.project_root / "pyproject.toml"
        if pyproj_file.exists():
             deps.extend(PyProjectParser(pyproj_file).parse())
             
        return deps
        
    def check_updates(self, dry_run: bool = True):
        """
        Main entry point to check and apply updates.
        1. Scan
        2. Analyze (Agent) - Placeholder for now
        3. Report / Apply
        """
        deps = self.scan_dependencies()
        print(f"Found {len(deps)} dependencies.")
        for dep in deps:
            print(f" - {dep.name} {dep.specifier} ({dep.source_file})")
            
        # Placeholder for agent invocation
        # state = {"dependencies": deps, "proposals": [], "errors": []}
        # result = graph_builder().invoke(state)
        
        if not dry_run:
            # logic to apply updates
            pass
