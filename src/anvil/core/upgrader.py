from pathlib import Path
import os
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from anvil.core.models import Dependency, UpdateProposal
from anvil.core.parsers.requirements import RequirementsParser
from anvil.core.parsers.pyproject import PyProjectParser
from anvil.tools.package import PackageManager
from anvil.tools.runner import TestRunner
from anvil.retrievers.main import ChangelogRetriever
from anvil.retrievers.pypi import PyPIRetriever
from anvil.core.logging import get_logger
from anvil.core.env import EnvironmentChecker # New component

logger = get_logger("upgrader")
console = Console()

class Upgrader:
    """Orchestrates the upgrade process."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        logger.debug(f"Initialized Upgrader for path: {self.project_root}")
        self.package_manager = PackageManager(self.project_root)
        self.test_runner = TestRunner(self.project_root)
        self.retriever = ChangelogRetriever()
        self.pypi = PyPIRetriever()
        self.env_checker = EnvironmentChecker(project_root)
        
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
        """
        logger.info("Starting dependency check...")
        deps = self.scan_dependencies()
        
        table = Table(title="Dependency Analysis")
        table.add_column("Package", style="cyan")
        table.add_column("Range", style="dim")
        table.add_column("Installed", style="magenta")
        table.add_column("Latest", style="green")
        table.add_column("Status", justify="center")
        table.add_column("Notes", style="dim")

        for dep in deps:
            logger.debug(f"Processing {dep.name}...")
            
            # 1. Get Versions
            latest_version = self.pypi.get_latest_version(dep.name)
            installed_version = self.env_checker.get_installed_version(dep.name)
            current_range = dep.current_version or "any"
            
            status_icon = "❓"
            notes = ""
            
            # 2. Compare Versions
            if not installed_version:
                notes = "Not installed"
                status_icon = "⚠️" 
            elif latest_version:
                if latest_version == installed_version:
                    status_icon = "✅" 
                    notes = "Up to date"
                else:
                    status_icon = "⬆️"
                    notes = "Upgrade available"
            else:
                 notes = "Package not found on PyPI"

            # 3. Source URL (Log only)
            source_url = self.retriever.get_source_url(dep.name)
            if source_url:
                logger.info(f"{dep.name}: Source found -> {source_url}")
            
            table.add_row(
                dep.name,
                current_range,
                installed_version or "missing",
                latest_version or "N/A", 
                status_icon, 
                notes
            )
            
        console.print(table)

    def interactive_upgrade(self):
        """
        Launches interactive TUI for upgrade selection.
        """
        try:
            from anvil.ui.dashboard import DependencyDashboard
        except ImportError:
            logger.error("The 'textual' library is required for interactive mode but is not installed.")
            console.print("[red]Error: 'textual' is missing.[/red]")
            console.print("Please install it to use the interactive upgrader:")
            console.print("  [bold]pip install textual[/bold]")
            return
        
        logger.info("Scanning for interactive upgrade...")
        deps = self.scan_dependencies()
        
        # Prepare data for dashboard
        dashboard_data = []
        for dep in deps:
            # 1. Get Versions (reuse logic efficiently?)
            # Ideally fetch in parallel or show loading state. For now, sequential block.
            logger.debug(f"Fetching data for {dep.name}...")
            
            latest = self.pypi.get_latest_version(dep.name)
            installed = self.env_checker.get_installed_version(dep.name)
            
            status = "❓"
            if not installed:
                status = "⚠️"
            elif latest:
                if latest == installed:
                    status = "✅"
                else:
                    status = "⬆️"
            
            dashboard_data.append({
                "name": dep.name,
                "range": dep.current_version or "any",
                "installed": installed or "missing",
                "latest": latest or "N/A",
                "status": status
            })
            
        # Launch App
        app = DependencyDashboard(dashboard_data)
        selected_packages = app.run()
        
        if selected_packages:
            console.rule("[bold green]Impact Analysis[/bold green]")
            
            # 1. Build Graph
            from anvil.core.graph import DependencyGraph
            graph = DependencyGraph()
            graph.build()
            
            for pkg in selected_packages:
                console.print(f"\n[bold cyan]Analyzing {pkg}...[/bold cyan]")
                
                # Check Dependents
                dependents = graph.get_dependents(pkg)
                if dependents:
                    console.print(f"  ⚠️  [yellow]Dependents:[/yellow] {', '.join(dependents)}")
                else:
                    console.print(f"  ✅  [dim]No reverse dependencies found.[/dim]")
                    
                # Fetch Changelog
                # We need the 'Target Version' (Latest). 
                # Re-fetch or cache from dashboard_data? Re-fetch for safety.
                latest = self.pypi.get_latest_version(pkg)
                current = self.env_checker.get_installed_version(pkg)
                
                if latest and latest != current:
                    console.print(f"  📝 [blue]Fetching changelog ({current} -> {latest})...[/blue]")
                    try:
                        changelog = self.retriever.get_changelog(pkg, current, latest)
                    except Exception as e:
                        logger.error(f"Failed to fetch changelog for {pkg}: {e}")
                        changelog = None
                    
                    if changelog:
                        # Save full report
                        report_file = os.path.join(os.getcwd(), "IMPACT_REPORT.md")
                        with open(report_file, "w") as f:
                            f.write(f"# Impact Analysis: {pkg}\n")
                            f.write(f"Upgrade: `{current}` -> `{latest}`\n\n")
                            f.write(changelog)
                        
                        console.print(f"  ✅ [green]Full changelog saved to {report_file}[/green]\n")
                        
                        # Show full changelog properly formatted
                        from rich.markdown import Markdown
                        console.print(Markdown(changelog))
                    else:
                        console.print("  [dim]No changelog found.[/dim]")
                else:
                    console.print("  [green]Already up to date.[/green]")

        else:
            console.print("[yellow]No packages selected.[/yellow]")
