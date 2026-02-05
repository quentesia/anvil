from anvil.agent.state import UpgradeWorkflowState, PackageUpgradeState
from anvil.core.logging import get_logger

logger = get_logger("agent.nodes.select")


def select_node(state: UpgradeWorkflowState) -> dict:
    """
    Launches TUI for package selection.

    Input: dashboard_data
    Output: selected_packages, packages (initialized states)
    """
    try:
        from anvil.ui.dashboard import DependencyDashboard
    except ImportError:
        return {
            "errors": state.get("errors", []) + ["Textual library not installed"],
            "phase": "done"
        }

    # Convert dashboard_data to TUI format with emojis
    tui_data = []
    for item in state["dashboard_data"]:
        status_icon = {
            "UP_TO_DATE": "✅",
            "OUTDATED": "⬆️",
            "MISSING": "⚠️",
        }.get(item["status"], "❓")

        tui_data.append({
            "name": item["name"],
            "range": item["range"],
            "installed": item["installed"],
            "latest": item["latest"],
            "status": status_icon
        })

    app = DependencyDashboard(tui_data)
    selected = app.run() or []

    if not selected:
        logger.info("No packages selected")
        return {"phase": "done", "selected_packages": []}

    # Initialize package states
    packages = []
    for pkg_name in selected:
        # Find matching dashboard entry
        entry = next((d for d in state["dashboard_data"] if d["name"] == pkg_name), None)
        if entry:
            packages.append(PackageUpgradeState(
                name=pkg_name,
                current_version=entry["installed"],
                target_version=entry["latest"],
                changelog=None,
                assessment=None,
                multi_agent_assessment=None,
                approved=False,
                installed=False,
                tests_passed=None,
                committed=False,
                error=None
            ))

    return {
        "selected_packages": selected,
        "packages": packages,
        "current_index": 0,
        "phase": "analyze"
    }
