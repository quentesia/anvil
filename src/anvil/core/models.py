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
