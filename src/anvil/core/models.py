from typing import List, Optional
from pydantic import BaseModel, Field

class Version(BaseModel):
    """Represents a package version."""
    original: str
    major: int = 0
    minor: int = 0
    patch: int = 0
    
    def __str__(self) -> str:
        return self.original

class Dependency(BaseModel):
    """Represents a single dependency parsing result."""
    name: str
    current_version: Optional[str] = None
    specifier: str = ""
    source_file: str
    line_number: Optional[int] = None
    
    @property
    def key(self) -> str:
        return self.name.lower()

class UpdateProposal(BaseModel):
    """Represents a proposed update for a dependency."""
    dependency: Dependency
    target_version: str
    changelog_summary: Optional[str] = None
    breaking_change_risk: str = "unknown" # low, medium, high
    reasoning: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Update {self.dependency.name} from {self.dependency.current_version} to {self.target_version}"

from enum import Enum

class RiskLevel(str, Enum):
    POSITIVE = "positive" # Beneficial: New features, performance boost, security fix
    LOW = "low"       # Safe: Docs, chores, tests, additive features
    MEDIUM = "medium" # Caution: Behavior changes, minor refactors, performance tweaks
    HIGH = "high"     # Stop: Breaking changes, removals, signature changes

class BreakingChange(BaseModel):
    category: str = Field(description="Type of break: 'API Removal', 'Signature Change', 'Behavioral Change', etc.")
    description: str = Field(description="Concise explanation of what broke.")
    quote: str = Field(description="Exact quote from the changelog evidencing this.")

class ImpactAssessment(BaseModel):
    """Structured analysis of a dependency update."""
    summary: str = Field(description="Concise executive summary of what this update does.")
    breaking_changes: List[BreakingChange] = Field(default_factory=list, description="List of confirmed breaking changes. Empty if none.")
    risk_score: RiskLevel = Field(description="Overall risk level.")
    migration_guide: Optional[str] = Field(None, description="Detailed prompt for an AI agent to fix code if needed.")
    justification: str = Field(description="Strict Audit Log. MUST start with '## Usage Audit' and list checked symbols.")
