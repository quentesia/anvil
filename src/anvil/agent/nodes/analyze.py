import platform
import subprocess
import re
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from anvil.agent.state import UpgradeWorkflowState
from anvil.retrievers.main import ChangelogRetriever
from anvil.core.scanner import CodebaseScanner
from anvil.core.graph import DependencyGraph
from anvil.agent.agents import AgentOrchestrator
from anvil.agent.agents.base import AgentContext
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.analyze")
console = Console()


def _detect_project_python_version(project_root: Path) -> str:
    """
    Detect the Python version used by the TARGET project, not Anvil's Python.

    Checks in order:
    1. .python-version file (pyenv)
    2. pyproject.toml requires-python
    3. Run 'python --version' in project directory
    4. Fallback to Anvil's Python version
    """
    # 1. Check .python-version (pyenv)
    python_version_file = project_root / ".python-version"
    if python_version_file.exists():
        try:
            version = python_version_file.read_text().strip()
            logger.debug(f"Found .python-version: {version}")
            return version
        except Exception:
            pass

    # 2. Check pyproject.toml requires-python
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text()
            # Look for requires-python = ">=3.11" or similar
            match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                spec = match.group(1)
                # Extract version number from spec like ">=3.11" or ">=3.11,<4.0"
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', spec)
                if version_match:
                    version = version_match.group(1)
                    logger.debug(f"Found requires-python: {spec} -> {version}")
                    return version
        except Exception:
            pass

    # 3. Try running python --version in the project directory
    try:
        result = subprocess.run(
            ["python", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse "Python 3.13.2"
            match = re.search(r'Python\s+(\d+\.\d+\.\d+)', result.stdout)
            if match:
                version = match.group(1)
                logger.debug(f"Detected from python --version: {version}")
                return version
    except Exception:
        pass

    # 4. Fallback to Anvil's Python (not ideal)
    fallback = platform.python_version()
    logger.warning(f"Could not detect project Python version, using Anvil's: {fallback}")
    return fallback


def analyze_node(state: UpgradeWorkflowState) -> dict:
    """
    Fetches changelog and runs MULTI-AGENT AI analysis for current package.

    Uses parallel agents:
    - RiskAssessor: Breaking changes and API risks
    - SecurityAuditor: CVE and vulnerability analysis
    - CompatibilityChecker: Python/dependency compatibility

    Input: current_index, packages, project_root
    Output: updated packages[current_index] with changelog and multi_agent_assessment
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    console.print(f"\n[bold cyan]═══ Analyzing {pkg['name']} ═══[/bold cyan]")

    # 1. Check dependents
    graph = DependencyGraph()
    graph.build()
    dependents = graph.get_dependents(pkg["name"])
    if dependents:
        console.print(f"  [yellow]⚠ Dependents:[/yellow] {', '.join(dependents)}")

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
        console.print("  [dim]No changelog found - skipping AI analysis[/dim]")
        pkg["assessment"] = None
        pkg["multi_agent_assessment"] = None
        packages[idx] = pkg
        return {"packages": packages, "phase": "confirm"}

    # Show truncated changelog
    changelog_preview = pkg["changelog"][:2000]
    if len(pkg["changelog"]) > 2000:
        changelog_preview += "\n\n... (truncated)"
    console.print(Panel(Markdown(changelog_preview), title="Changelog Preview", border_style="dim"))

    # 3. Scan codebase usage
    scanner = CodebaseScanner(str(project_root))
    usage_context = scanner.scan_package_usage(pkg["name"])
    if usage_context:
        console.print(f"  [dim]Found {len(usage_context)} usages in codebase[/dim]")

    # 4. Get project config
    project_config = ""
    pyproj_path = project_root / "pyproject.toml"
    if pyproj_path.exists():
        try:
            project_config = pyproj_path.read_text()[:5000]
        except Exception:
            pass

    # 5. MULTI-AGENT ANALYSIS
    console.print("\n  [bold magenta]🤖 Running Multi-Agent Analysis...[/bold magenta]")
    console.print("     ├── RiskAssessor (breaking changes)")
    console.print("     ├── SecurityAuditor (CVE/vulnerabilities)")
    console.print("     └── CompatibilityChecker (Python/deps)")

    # Detect project's Python version (not Anvil's!)
    python_version = _detect_project_python_version(project_root)
    console.print(f"  [dim]Project Python version: {python_version}[/dim]")

    # Build context for agents
    context = AgentContext(
        package_name=pkg["name"],
        current_version=pkg["current_version"],
        target_version=pkg["target_version"],
        changelog=pkg["changelog"],
        usage_context=usage_context or [],
        python_version=python_version,
        project_config=project_config
    )

    # Run orchestrator (parallel by default)
    orchestrator = AgentOrchestrator(parallel=True)
    multi_assessment = orchestrator.analyze(context)

    # Store both old-style and new multi-agent assessment for compatibility
    pkg["multi_agent_assessment"] = multi_assessment.model_dump()
    pkg["assessment"] = None  # Clear old single-agent assessment

    # 6. Display Multi-Agent Results
    _display_multi_agent_results(multi_assessment)

    packages[idx] = pkg

    # Route based on overall risk
    if multi_assessment.overall_risk.value == "high" or multi_assessment.blocking_issues:
        return {"packages": packages, "phase": "confirm"}
    else:
        return {"packages": packages, "phase": "confirm"}


def _display_multi_agent_results(assessment):
    """Display multi-agent assessment results."""
    console.print()

    # Agent status table - no_wrap=False allows text to wrap naturally
    status_table = Table(title="Agent Results", show_header=True, header_style="bold", expand=True)
    status_table.add_column("Agent", style="cyan", width=15)
    status_table.add_column("Status", justify="center", width=12)
    status_table.add_column("Key Finding", no_wrap=False)

    # Risk Assessor
    if assessment.risk:
        risk_color = {"positive": "cyan", "low": "green", "medium": "yellow", "high": "red"}.get(
            assessment.risk.risk_level.value, "white"
        )
        status_table.add_row(
            "RiskAssessor",
            f"[{risk_color}]{assessment.risk.risk_level.value.upper()}[/{risk_color}]",
            assessment.risk.summary
        )
    else:
        status_table.add_row("RiskAssessor", "[red]FAILED[/red]", "-")

    # Security Auditor
    if assessment.security:
        sec_color = {"safe": "green", "improved": "cyan", "neutral": "white", "concerning": "yellow"}.get(
            assessment.security.security_score, "white"
        )
        status_table.add_row(
            "SecurityAuditor",
            f"[{sec_color}]{assessment.security.security_score.upper()}[/{sec_color}]",
            assessment.security.summary
        )
    else:
        status_table.add_row("SecurityAuditor", "[red]FAILED[/red]", "-")

    # Compatibility
    if assessment.compatibility:
        compat_status = "✅ COMPATIBLE" if assessment.compatibility.compatible else "❌ INCOMPATIBLE"
        compat_color = "green" if assessment.compatibility.compatible else "red"
        status_table.add_row(
            "Compatibility",
            f"[{compat_color}]{compat_status}[/{compat_color}]",
            assessment.compatibility.summary
        )
    else:
        status_table.add_row("Compatibility", "[red]FAILED[/red]", "-")

    console.print(status_table)

    # Overall assessment
    risk_colors = {"positive": "cyan", "low": "green", "medium": "yellow", "high": "red"}
    overall_color = risk_colors.get(assessment.overall_risk.value, "white")

    console.print(f"\n  [bold]Overall Risk:[/bold] [{overall_color}]{assessment.overall_risk.value.upper()}[/{overall_color}]")

    # Show blocking issues
    if assessment.blocking_issues:
        console.print("\n  [bold red]🛑 Blocking Issues:[/bold red]")
        for issue in assessment.blocking_issues:
            console.print(f"     • {issue}")

    # Show warnings
    if assessment.warnings:
        console.print("\n  [bold yellow]⚠️ Warnings:[/bold yellow]")
        for warning in assessment.warnings[:5]:  # Show first 5
            console.print(f"     • {warning}")
        if len(assessment.warnings) > 5:
            console.print(f"     ... and {len(assessment.warnings) - 5} more")

    # Show improvements
    if assessment.improvements:
        console.print("\n  [bold green]✅ Improvements:[/bold green]")
        for improvement in assessment.improvements[:3]:
            console.print(f"     • {improvement}")

    # Recommendation
    if assessment.upgrade_recommended:
        console.print("\n  [bold green]→ Upgrade RECOMMENDED[/bold green]")
    else:
        console.print("\n  [bold yellow]→ Review recommended before upgrade[/bold yellow]")

    # Human-readable summary
    _display_human_summary(assessment)


def _display_human_summary(assessment):
    """Display a consolidated human-readable summary for decision making."""
    console.print("\n" + "─" * 60)
    console.print("[bold]📋 Summary for Human Review[/bold]\n")

    # What's changing
    console.print("[bold underline]What's Changing:[/bold underline]")

    if assessment.risk and assessment.risk.breaking_changes:
        console.print("\n[yellow]Breaking Changes:[/yellow]")
        for bc in assessment.risk.breaking_changes:
            console.print(f"  • [{bc.severity.upper()}] {bc.description}")
            if bc.affected_symbols:
                console.print(f"    Affects your code: {', '.join(bc.affected_symbols)}")

    if assessment.risk and assessment.risk.behavioral_changes:
        console.print("\n[yellow]Behavioral Changes:[/yellow]")
        for change in assessment.risk.behavioral_changes:
            console.print(f"  • {change}")

    # Security updates
    if assessment.security:
        if assessment.security.vulnerabilities_fixed:
            console.print("\n[green]Security Fixes:[/green]")
            for vuln in assessment.security.vulnerabilities_fixed:
                if vuln.fixed_in_upgrade:
                    cve = f"[{vuln.cve_id}] " if vuln.cve_id else ""
                    console.print(f"  • {cve}{vuln.description}")

        if assessment.security.security_improvements:
            console.print("\n[green]Security Improvements:[/green]")
            for imp in assessment.security.security_improvements[:3]:
                console.print(f"  • {imp}")

    # Compatibility notes
    if assessment.compatibility:
        if assessment.compatibility.min_python_version:
            console.print(f"\n[dim]Minimum Python: {assessment.compatibility.min_python_version}[/dim]")

        if assessment.compatibility.deprecated_features_used:
            console.print("\n[yellow]Deprecations affecting your code:[/yellow]")
            for dep in assessment.compatibility.deprecated_features_used:
                console.print(f"  • {dep}")

        if assessment.compatibility.dependency_changes:
            console.print("\n[dim]Dependency changes:[/dim]")
            for change in assessment.compatibility.dependency_changes[:3]:
                console.print(f"  • {change}")

    # Migration required?
    if assessment.risk and assessment.risk.migration_required:
        console.print("\n[bold yellow]⚠️ Code changes may be required![/bold yellow]")
        if assessment.risk.migration_guide:
            console.print("\n[bold]Migration Guide:[/bold]")
            console.print(Panel(assessment.risk.migration_guide, border_style="yellow"))

    # Final verdict
    console.print("\n[bold underline]Bottom Line:[/bold underline]")
    if not assessment.blocking_issues and not (assessment.risk and assessment.risk.breaking_changes):
        console.print("  [green]✓ Safe to upgrade - no breaking changes detected[/green]")
    elif assessment.blocking_issues:
        console.print("  [red]✗ Do not upgrade - blocking issues found[/red]")
    elif assessment.risk and assessment.risk.migration_required:
        console.print("  [yellow]⚡ Upgrade possible but requires code changes[/yellow]")
    else:
        console.print("  [yellow]⚠ Review the changes above before proceeding[/yellow]")

    console.print("─" * 60)
