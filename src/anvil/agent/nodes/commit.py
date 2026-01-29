from pathlib import Path
from rich.console import Console
from anvil.agent.state import UpgradeWorkflowState
from anvil.tools.package import PackageManager
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.commit")
console = Console()


def commit_node(state: UpgradeWorkflowState) -> dict:
    """
    Commits upgrade by updating manifest files.

    Input: current package, project_root
    Output: committed flag, next phase
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    console.print("  [blue]Updating manifest...[/blue]")

    pm = PackageManager(project_root)
    success = pm.install(pkg["name"], pkg["target_version"], update_manifest=True)

    if success:
        console.print("  [bold green]Upgrade committed![/bold green]")
        pkg["committed"] = True
        packages[idx] = pkg
        completed = list(state.get("completed", [])) + [pkg["name"]]
        return {"packages": packages, "completed": completed, "phase": "next"}
    else:
        console.print("  [yellow]Manifest update failed, but package is installed[/yellow]")
        pkg["error"] = "Manifest update failed"
        packages[idx] = pkg
        completed = list(state.get("completed", [])) + [pkg["name"]]
        return {"packages": packages, "completed": completed, "phase": "next"}
