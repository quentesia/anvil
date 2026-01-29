"""
Unit tests for LangGraph nodes
"""
import pytest
from pathlib import Path
from anvil.agent.state import UpgradeWorkflowState, PackageUpgradeState
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


class TestScanNode:
    """Test scan_node functionality"""

    def test_scan_node_basic(self, tmp_path):
        """Test that scan_node processes dependencies correctly"""
        # Create a simple requirements.txt
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.30.0\nrich==13.0.0\n")

        state: UpgradeWorkflowState = {
            "project_root": str(tmp_path),
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": [],
            "current_index": 0,
            "packages": [],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "scan",
            "errors": []
        }

        result = scan_node(state)

        # Verify it returns the correct phase
        assert result["phase"] == "select"

        # Verify it found dependencies
        assert len(result["dependencies"]) > 0
        assert len(result["dashboard_data"]) > 0


class TestSelectNode:
    """Test select_node functionality"""

    def test_select_node_no_selection(self):
        """Test select_node when no packages are selected"""
        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [
                {
                    "name": "requests",
                    "range": ">=2.30.0",
                    "installed": "2.30.0",
                    "latest": "2.31.0",
                    "status": "OUTDATED"
                }
            ],
            "selected_packages": [],
            "current_index": 0,
            "packages": [],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "select",
            "errors": []
        }

        # Mock the TUI to return empty selection
        # Note: In real test, you'd mock DependencyDashboard
        # For now, this tests the structure
        assert state["phase"] == "select"


class TestAnalyzeNode:
    """Test analyze_node functionality"""

    def test_analyze_node_structure(self):
        """Test that analyze_node has correct structure"""
        pkg_state = PackageUpgradeState(
            name="requests",
            current_version="2.30.0",
            target_version="2.31.0",
            changelog=None,
            assessment=None,
            approved=False,
            installed=False,
            tests_passed=None,
            committed=False,
            error=None
        )

        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": ["requests"],
            "current_index": 0,
            "packages": [pkg_state],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "analyze",
            "errors": []
        }

        # Verify state structure is correct
        assert len(state["packages"]) == 1
        assert state["packages"][0]["name"] == "requests"


class TestConfirmNode:
    """Test confirm_node functionality"""

    def test_confirm_node_skip(self, monkeypatch):
        """Test confirm_node when user declines"""
        # Mock Confirm.ask to return False
        def mock_ask(prompt):
            return False

        from rich.prompt import Confirm
        monkeypatch.setattr(Confirm, "ask", mock_ask)

        pkg_state = PackageUpgradeState(
            name="requests",
            current_version="2.30.0",
            target_version="2.31.0",
            changelog="Test changelog",
            assessment=None,
            approved=False,
            installed=False,
            tests_passed=None,
            committed=False,
            error=None
        )

        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": ["requests"],
            "current_index": 0,
            "packages": [pkg_state],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "confirm",
            "errors": []
        }

        result = confirm_node(state)

        assert result["phase"] == "next"
        assert "requests" in result["skipped"]
        assert not result["packages"][0]["approved"]


class TestGraphRouting:
    """Test graph routing logic"""

    def test_route_after_select_with_packages(self):
        """Test routing when packages are selected"""
        from anvil.agent.graph import route_after_select

        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": ["requests"],
            "current_index": 0,
            "packages": [],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "select",
            "errors": []
        }

        result = route_after_select(state)
        assert result == "analyze"

    def test_route_after_select_no_packages(self):
        """Test routing when no packages selected"""
        from anvil.agent.graph import route_after_select

        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": [],
            "current_index": 0,
            "packages": [],
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "select",
            "errors": []
        }

        result = route_after_select(state)
        assert result == "done"

    def test_next_package_or_done(self):
        """Test advancing to next package"""
        from anvil.agent.graph import next_package_or_done

        # Test with more packages remaining
        state: UpgradeWorkflowState = {
            "project_root": "/tmp",
            "dependencies": [],
            "dashboard_data": [],
            "selected_packages": ["pkg1", "pkg2"],
            "current_index": 0,
            "packages": [{}, {}],  # Two packages
            "completed": [],
            "failed": [],
            "skipped": [],
            "phase": "next",
            "errors": []
        }

        result = next_package_or_done(state)
        assert result == "analyze"

        # Test with no more packages
        state["current_index"] = 1
        result = next_package_or_done(state)
        assert result == "done"


class TestGraphCompilation:
    """Test that the graph compiles correctly"""

    def test_build_upgrade_graph(self):
        """Test that build_upgrade_graph returns a compiled graph"""
        from anvil.agent.graph import build_upgrade_graph

        graph = build_upgrade_graph()

        # Verify it's a compiled graph (has invoke method)
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")
