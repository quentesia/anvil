from pathlib import Path
from anvil.agent.state import UpgradeWorkflowState
from anvil.core.parsers.requirements import RequirementsParser
from anvil.core.parsers.pyproject import PyProjectParser
from anvil.retrievers.pypi import PyPIRetriever
from anvil.core.env import EnvironmentChecker
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.scan")


def scan_node(state: UpgradeWorkflowState) -> dict:
    """
    Scans project for dependencies and fetches version info.

    Input: project_root
    Output: dependencies, dashboard_data
    """
    project_root = Path(state["project_root"])
    pypi = PyPIRetriever()
    env_checker = EnvironmentChecker(str(project_root))

    deps = []

    # Parse requirements.txt
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        logger.debug("Parsing requirements.txt...")
        deps.extend(RequirementsParser(req_file).parse())

    # Parse pyproject.toml
    pyproj_file = project_root / "pyproject.toml"
    if pyproj_file.exists():
        logger.debug("Parsing pyproject.toml...")
        deps.extend(PyProjectParser(pyproj_file).parse())

    logger.info(f"Found {len(deps)} dependencies")

    # Build dashboard data
    dashboard_data = []
    for dep in deps:
        latest = pypi.get_latest_version(dep.name)
        installed = env_checker.get_installed_version(dep.name)

        status = "?"
        if not installed:
            status = "MISSING"
        elif latest:
            status = "UP_TO_DATE" if latest == installed else "OUTDATED"

        dashboard_data.append({
            "name": dep.name,
            "range": dep.current_version or "any",
            "installed": installed or "missing",
            "latest": latest or "N/A",
            "status": status
        })

    return {
        "dependencies": deps,
        "dashboard_data": dashboard_data,
        "phase": "select"
    }
