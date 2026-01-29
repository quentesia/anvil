from pathlib import Path
from rich.console import Console
from anvil.agent.state import UpgradeWorkflowState
from anvil.tools.runner import TestRunner
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.test")
console = Console()


def run_tests_node(state: UpgradeWorkflowState) -> dict:
    """
    Runs project tests to verify upgrade.

    Input: project_root
    Output: tests_passed flag, next phase
    """
    idx = state["current_index"]
    packages = list(state["packages"])
    pkg = dict(packages[idx])
    project_root = Path(state["project_root"])

    console.print("  [blue]Running tests...[/blue]")

    runner = TestRunner(project_root)
    success, output = runner.run_tests()

    pkg["tests_passed"] = success
    packages[idx] = pkg

    if success:
        console.print("  [bold green]Tests PASSED![/bold green]")
        return {"packages": packages, "phase": "commit"}
    else:
        console.print("  [bold red]Tests FAILED![/bold red]")
        console.print(f"  [dim]{output[-500:]}[/dim]")
        return {"packages": packages, "phase": "rollback"}
