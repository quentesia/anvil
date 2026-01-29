#!/usr/bin/env python3
"""
Visualize the LangGraph upgrade workflow
"""
from anvil.agent.graph import build_upgrade_graph

def main():
    graph = build_upgrade_graph()

    # Print graph structure
    print("Upgrade Workflow Graph")
    print("=" * 50)
    print("\nNodes:")
    print("  - scan: Scans project dependencies")
    print("  - select: TUI package selection")
    print("  - analyze: Changelog + AI risk assessment")
    print("  - confirm: User confirmation")
    print("  - install: Trial installation")
    print("  - test: Run pytest")
    print("  - commit: Update manifest")
    print("  - rollback: Revert on failure")
    print("  - next: Advance to next package")
    print("  - done: Summary")

    print("\n" + "=" * 50)
    print("Graph compiled successfully!")
    print(f"Type: {type(graph)}")

    # Try to get mermaid visualization if available
    try:
        mermaid = graph.get_graph().draw_mermaid()
        print("\nMermaid Diagram:")
        print(mermaid)
    except Exception as e:
        print(f"\nCould not generate mermaid diagram: {e}")

if __name__ == "__main__":
    main()
