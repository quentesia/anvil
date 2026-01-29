from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from anvil.agent.state import UpgradeWorkflowState
from anvil.tools.package import PackageManager
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.rollback")
console = Console()


def rollback_node(state: UpgradeWorkflowState) -> dict:
    """
    Handles rollback after test failure.

    Input: current package, project_root
    Output: next phase
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    if Confirm.ask(f"Tests failed. Rollback to {pkg['current_version']}?"):
        console.print(f"  [blue]Rolling back to {pkg['name']}=={pkg['current_version']}...[/blue]")

        pm = PackageManager(project_root)
        success = pm.install(pkg["name"], pkg["current_version"], update_manifest=False)

        if success:
            console.print("  [green]Rollback successful[/green]")
        else:
            console.print("  [red]Rollback failed![/red]")
            pkg["error"] = "Rollback failed"
    else:
        console.print("  [yellow]Keeping failed upgrade[/yellow]")

    packages[idx] = pkg
    failed = list(state.get("failed", [])) + [pkg["name"]]
    return {"packages": packages, "failed": failed, "phase": "next"}
