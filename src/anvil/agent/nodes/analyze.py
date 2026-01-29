import platform
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from anvil.agent.state import UpgradeWorkflowState
from anvil.retrievers.main import ChangelogRetriever
from anvil.core.scanner import CodebaseScanner
from anvil.core.graph import DependencyGraph
from anvil.agent.brain import RiskAssessor
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.analyze")
console = Console()


def analyze_node(state: UpgradeWorkflowState) -> dict:
    """
    Fetches changelog and runs AI risk assessment for current package.

    Input: current_index, packages, project_root
    Output: updated packages[current_index] with changelog and assessment
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    console.print(f"\n[bold cyan]Analyzing {pkg['name']}...[/bold cyan]")

    # 1. Check dependents
    graph = DependencyGraph()
    graph.build()
    dependents = graph.get_dependents(pkg["name"])
    if dependents:
        console.print(f"  [yellow]Dependents:[/yellow] {', '.join(dependents)}")

    # 2. Fetch changelog
    retriever = ChangelogRetriever()
    try:
        changelog = retriever.get_changelog(
            pkg["name"],
            pkg["current_version"],
            pkg["target_version"]
        )
        pkg["changelog"] = changelog
    except Exception as e:
        logger.error(f"Changelog fetch failed: {e}")
        pkg["changelog"] = None

    if not pkg["changelog"]:
        console.print("  [dim]No changelog found[/dim]")
        # Still allow upgrade without changelog
        pkg["assessment"] = None
        packages[idx] = pkg
        return {"packages": packages, "phase": "confirm"}

    console.print(Markdown(pkg["changelog"][:2000] + "..." if len(pkg["changelog"]) > 2000 else pkg["changelog"]))

    # 3. Scan codebase usage
    scanner = CodebaseScanner(str(project_root))
    usage_context = scanner.scan_package_usage(pkg["name"])
    if usage_context:
        console.print(f"  [dim]Found {len(usage_context)} usages[/dim]")

    # 4. Get project config
    project_config = ""
    pyproj_path = project_root / "pyproject.toml"
    if pyproj_path.exists():
        try:
            project_config = pyproj_path.read_text()[:5000]
        except Exception:
            pass

    # 5. AI Analysis
    console.print("  [magenta]Running AI analysis...[/magenta]")
    brain = RiskAssessor()
    assessment = brain.assess_changelog(
        pkg["name"],
        pkg["current_version"],
        pkg["target_version"],
        pkg["changelog"],
        usage_context=usage_context,
        python_version=platform.python_version(),
        project_config=project_config
    )
    pkg["assessment"] = assessment

    # 6. Display results
    if assessment:
        risk_colors = {
            "positive": "cyan",
            "low": "green",
            "medium": "yellow",
            "high": "red"
        }
        color = risk_colors.get(assessment.risk_score.value, "white")
        console.print(f"\n  [bold {color}]Risk: {assessment.risk_score.value.upper()}[/bold {color}]")
        console.print(f"  {assessment.summary}")

        if assessment.breaking_changes:
            console.print("  [bold red]Breaking Changes:[/bold red]")
            for bc in assessment.breaking_changes:
                console.print(f"    - {bc.category}: {bc.description}")

    packages[idx] = pkg

    # Route based on risk
    if assessment and assessment.risk_score.value == "high":
        return {"packages": packages, "phase": "confirm"}
    else:
        # Auto-approve for low/medium/positive risk
        return {"packages": packages, "phase": "confirm"}  # Can change to auto_approve later
