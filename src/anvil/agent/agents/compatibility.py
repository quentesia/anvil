from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from anvil.agent.agents.base import BaseAgent


class CompatibilityIssue(BaseModel):
    """Details about a compatibility issue."""
    category: str = Field(description="'python_version', 'dependency_conflict', 'platform', 'deprecation'")
    description: str = Field(description="What the compatibility issue is")
    severity: str = Field(description="'blocking', 'warning', 'info'")
    workaround: Optional[str] = Field(None, description="Potential workaround if available")


class CompatibilityAssessment(BaseModel):
    """Compatibility assessment from the CompatibilityAgent."""
    summary: str = Field(description="Compatibility summary")
    compatible: bool = Field(description="Whether upgrade is compatible with current environment")
    python_compatible: bool = Field(description="Whether Python version is supported")
    min_python_version: Optional[str] = Field(None, description="Minimum Python version required by target")
    max_python_version: Optional[str] = Field(None, description="Maximum Python version supported by target")
    issues: List[CompatibilityIssue] = Field(default_factory=list)
    deprecated_features_used: List[str] = Field(default_factory=list, description="Deprecated features the user might be using")
    dependency_changes: List[str] = Field(default_factory=list, description="Notable dependency requirement changes")
    confidence: float = Field(description="Confidence in assessment (0.0-1.0)")


COMPAT_SYSTEM_PROMPT = """You are a Python Compatibility Expert specializing in dependency management.

Your job: Analyze changelogs for COMPATIBILITY issues that might prevent successful upgrades.

## CRITICAL: Python Version Comparison Rules

When checking Python version compatibility, use CORRECT version comparison logic:

- "Requires Python >= 3.10" means 3.10, 3.11, 3.12, 3.13, etc. are ALL COMPATIBLE
- "Requires Python >= 3.10" with user on 3.13.2 → COMPATIBLE (3.13 >= 3.10)
- "Requires Python < 3.12" with user on 3.13.2 → INCOMPATIBLE (3.13 >= 3.12)
- "Dropped support for Python 3.8" with user on 3.13.2 → COMPATIBLE (doesn't affect them)

**IMPORTANT**: Higher Python versions are NEWER. If min version is 3.10 and user has 3.13, they are COMPATIBLE.

## What to Look For

1. **Python Version Requirements**:
   - Minimum Python version changes (e.g., "Now requires Python 3.9+")
   - Maximum Python version support (rare, but check for it)
   - Dropped Python version support (only affects users on OLD versions)

2. **Dependency Changes**:
   - New required dependencies
   - Removed dependencies
   - Changed version constraints
   - Conflicts with common packages

3. **Platform Compatibility**:
   - OS-specific changes
   - Architecture requirements (ARM, x86, etc.)
   - Environment requirements

4. **Deprecations**:
   - Features marked as deprecated
   - Removal timelines
   - Migration paths

## Assessment Guidelines

- ONLY flag python_compatible=false if user's version is LOWER than minimum OR HIGHER than maximum
- If changelog says "requires >= 3.10" and user has 3.13, set python_compatible=true
- Flag blocking issues ONLY for actual incompatibilities, not hypothetical ones
- When in doubt about version support, assume compatible=true
"""

COMPAT_USER_PROMPT = """Analyze the compatibility of upgrading `{package_name}` from `{current_version}` to `{target_version}`.

## User's Environment
- **Python Version**: {python_version}
- **Project Configuration**:
{project_config}

## User's Usage
{usage_context}

## Changelog
{changelog_text}

---
**TASK**:
1. Check if the target version is compatible with Python {python_version}
   - If changelog says "requires Python >= X.Y" and {python_version} >= X.Y, it IS compatible
   - Example: "requires >= 3.10" + user has 3.13.2 = COMPATIBLE (3.13 > 3.10)
   - Only mark incompatible if user version is LOWER than minimum required
2. Identify any dependency conflicts or changes
3. Flag deprecations that affect the user's code
4. Determine if the upgrade will work in this environment

REMEMBER: {python_version} is the user's version. If package requires >= 3.10 and user has 3.13.2, that is COMPATIBLE.
"""

COMPAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", COMPAT_SYSTEM_PROMPT),
    ("human", COMPAT_USER_PROMPT),
])


class CompatibilityAgent(BaseAgent[CompatibilityAssessment]):
    """
    Analyzes changelogs for compatibility issues.

    Checks Python version compatibility, dependency conflicts,
    platform requirements, and deprecations.
    """

    name = "compatibility"
    description = "Analyzes compatibility and dependency conflicts"

    @property
    def output_schema(self) -> type[CompatibilityAssessment]:
        return CompatibilityAssessment

    def get_prompt(self):
        return COMPAT_PROMPT
