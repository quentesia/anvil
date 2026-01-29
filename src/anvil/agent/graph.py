from typing import Literal
from langgraph.graph import StateGraph, END
from anvil.agent.state import UpgradeWorkflowState
from anvil.agent.nodes import (
    scan_node,
    select_node,
    analyze_node,
    confirm_node,
    install_node,
    run_tests_node,
    commit_node,
    rollback_node,
)


def route_after_select(state: UpgradeWorkflowState) -> Literal["analyze", "done"]:
    """Routes based on whether packages were selected."""
    if state.get("selected_packages"):
        return "analyze"
    return "done"


def route_after_phase(state: UpgradeWorkflowState) -> str:
    """Routes based on current phase."""
    return state.get("phase", "done")


def next_package_or_done(state: UpgradeWorkflowState) -> Literal["analyze", "done"]:
    """Advances to next package or ends."""
    idx = state.get("current_index", 0)
    packages = state.get("packages", [])

    if idx + 1 < len(packages):
        return "analyze"
    return "done"


def next_node(state: UpgradeWorkflowState) -> dict:
    """Advances current_index to next package."""
    return {
        "current_index": state.get("current_index", 0) + 1,
        "phase": "analyze"
    }


def done_node(state: UpgradeWorkflowState) -> dict:
    """Final summary node."""
    from rich.console import Console
    console = Console()

    completed = state.get("completed", [])
    failed = state.get("failed", [])
    skipped = state.get("skipped", [])

    console.print("\n[bold]Upgrade Summary[/bold]")
    if completed:
        console.print(f"  [green]Completed:[/green] {', '.join(completed)}")
    if failed:
        console.print(f"  [red]Failed:[/red] {', '.join(failed)}")
    if skipped:
        console.print(f"  [yellow]Skipped:[/yellow] {', '.join(skipped)}")

    return {"phase": "done"}


def build_upgrade_graph():
    """Builds and compiles the upgrade workflow graph."""
    graph = StateGraph(UpgradeWorkflowState)

    # Add nodes
    graph.add_node("scan", scan_node)
    graph.add_node("select", select_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("install", install_node)
    graph.add_node("test", run_tests_node)
    graph.add_node("commit", commit_node)
    graph.add_node("rollback", rollback_node)
    graph.add_node("next", next_node)
    graph.add_node("done", done_node)

    # Set entry point
    graph.set_entry_point("scan")

    # Add edges
    graph.add_edge("scan", "select")
    graph.add_conditional_edges(
        "select",
        route_after_select,
        {"analyze": "analyze", "done": "done"}
    )

    # After analyze, route based on phase
    graph.add_conditional_edges(
        "analyze",
        route_after_phase,
        {"confirm": "confirm", "done": "done"}
    )

    # After confirm
    graph.add_conditional_edges(
        "confirm",
        route_after_phase,
        {"install": "install", "next": "next"}
    )

    # After install
    graph.add_conditional_edges(
        "install",
        route_after_phase,
        {"test": "test", "next": "next"}
    )

    # After test
    graph.add_conditional_edges(
        "test",
        route_after_phase,
        {"commit": "commit", "rollback": "rollback"}
    )

    # After commit/rollback -> next
    graph.add_edge("commit", "next")
    graph.add_edge("rollback", "next")

    # After next, either loop or done
    graph.add_conditional_edges(
        "next",
        next_package_or_done,
        {"analyze": "analyze", "done": "done"}
    )

    # Done is terminal
    graph.add_edge("done", END)

    return graph.compile()


# Backwards-compatible function
def builder():
    """Legacy builder function."""
    return build_upgrade_graph()
