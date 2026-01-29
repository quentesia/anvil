from rich.console import Console
from rich.prompt import Confirm
from anvil.agent.state import UpgradeWorkflowState
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.confirm")
console = Console()


def confirm_node(state: UpgradeWorkflowState) -> dict:
    """
    Asks user for confirmation to proceed with upgrade.

    Input: current package
    Output: approved flag, next phase
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])

    console.print(f"\n[bold]Upgrade {pkg['name']}: {pkg['current_version']} -> {pkg['target_version']}[/bold]")

    if Confirm.ask("Proceed with installation?"):
        pkg["approved"] = True
        packages[idx] = pkg
        return {"packages": packages, "phase": "install"}
    else:
        pkg["approved"] = False
        packages[idx] = pkg
        skipped = list(state.get("skipped", [])) + [pkg["name"]]
        return {"packages": packages, "skipped": skipped, "phase": "next"}
