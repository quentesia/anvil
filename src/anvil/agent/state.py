from typing import List, Optional, TypedDict, Literal
from anvil.core.models import Dependency, ImpactAssessment


class PackageUpgradeState(TypedDict):
    """State for a single package being upgraded."""
    name: str
    current_version: str
    target_version: str
    changelog: Optional[str]
    assessment: Optional[ImpactAssessment]  # Legacy single-agent assessment
    multi_agent_assessment: Optional[dict]  # New multi-agent assessment (serialized)
    approved: bool
    installed: bool
    tests_passed: Optional[bool]
    committed: bool
    error: Optional[str]


class UpgradeWorkflowState(TypedDict):
    """Main graph state."""
    # Input
    project_root: str

    # Scanning phase
    dependencies: List[Dependency]
    dashboard_data: List[dict]  # For TUI display

    # Selection phase
    selected_packages: List[str]

    # Processing phase (current package index)
    current_index: int
    packages: List[PackageUpgradeState]

    # Results
    completed: List[str]  # Successfully upgraded
    failed: List[str]     # Failed upgrades
    skipped: List[str]    # User skipped

    # Control flow
    phase: Literal["scan", "select", "analyze", "confirm", "install", "test", "commit", "rollback", "next", "done"]

    # Error handling
    errors: List[str]
