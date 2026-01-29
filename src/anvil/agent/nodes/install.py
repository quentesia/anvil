from pathlib import Path
from rich.console import Console
from anvil.agent.state import UpgradeWorkflowState
from anvil.tools.package import PackageManager
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.install")
console = Console()


def install_node(state: UpgradeWorkflowState) -> dict:
    """
    Performs trial installation (environment only, no manifest update).

    Input: current package, project_root
    Output: installed flag, next phase
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    console.print(f"  [blue]Installing {pkg['name']}=={pkg['target_version']} (trial)...[/blue]")

    pm = PackageManager(project_root)
    success = pm.install(pkg["name"], pkg["target_version"], update_manifest=False)

    if success:
        console.print("  [green]Trial installation successful[/green]")
        pkg["installed"] = True
        packages[idx] = pkg
        return {"packages": packages, "phase": "test"}
    else:
        console.print("  [red]Installation failed[/red]")
        pkg["error"] = "Installation failed"
        packages[idx] = pkg
        failed = list(state.get("failed", [])) + [pkg["name"]]
        return {"packages": packages, "failed": failed, "phase": "next"}
