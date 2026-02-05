from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from anvil.agent.agents.base import BaseAgent
from anvil.core.models import RiskLevel


class BreakingChangeDetail(BaseModel):
    """Details about a specific breaking change."""
    category: str = Field(description="Type: 'API Removal', 'Signature Change', 'Behavioral Change', 'Deprecation'")
    description: str = Field(description="What changed and how it might break code")
    severity: str = Field(description="'critical', 'major', or 'minor'")
    affected_symbols: List[str] = Field(default_factory=list, description="Symbols from user's code that are affected")


class RiskAssessment(BaseModel):
    """Risk assessment from the RiskAssessor agent."""
    summary: str = Field(description="Concise summary of upgrade risks")
    risk_level: RiskLevel = Field(description="Overall risk: positive, low, medium, high")
    breaking_changes: List[BreakingChangeDetail] = Field(default_factory=list)
    behavioral_changes: List[str] = Field(default_factory=list, description="Subtle behavior changes that might affect code")
    migration_required: bool = Field(description="Whether code changes are needed")
    migration_guide: Optional[str] = Field(None, description="Steps to migrate if needed")
    confidence: float = Field(description="Confidence in assessment (0.0-1.0)")


RISK_SYSTEM_PROMPT = """You are a Principal Software Engineer specializing in dependency risk analysis.

Your job: Analyze changelogs to identify BREAKING CHANGES and BEHAVIORAL SHIFTS that could affect production code.

## CRITICAL: Python Version Logic

When changelog mentions Python version requirements:
- "Requires Python >= 3.11" means 3.11, 3.12, 3.13+ are ALL SUPPORTED
- If user has Python 3.13 and package requires >= 3.11, this is NOT a breaking change (3.13 > 3.11)
- "Dropped support for Python 3.8" only affects users on Python 3.8 or lower
- NEVER mark Python version as HIGH risk if user's version EXCEEDS the minimum requirement

## Analysis Guidelines

1. **Be Evidence-Based**: Only cite risks that appear in the changelog. Don't invent problems.

2. **Look Beyond Headers**: Breaking changes hide in:
   - Renamed functions/arguments
   - Changed default values
   - Modified return types
   - "Bug fixes" that change expected behavior

3. **Risk Levels**:
   - POSITIVE: Security fixes, performance improvements, new features (no breaking changes)
   - LOW: Docs, tests, additive features only, Python version drops that DON'T affect user
   - MEDIUM: Behavior changes, deprecations, minor API tweaks
   - HIGH: Removed APIs the user actually uses, signature changes to used functions

4. **User Context**: Check if the user's actual code uses affected symbols. If not, it's LOW risk.

5. **Confidence**: Rate your confidence based on changelog clarity. Vague changelogs = lower confidence.

## IMPORTANT
- Dropping old Python versions (3.8, 3.9, 3.10) is NOT a risk for users on newer Python (3.11+)
- Build tool changes (cibuildwheel, setuptools) are NOT runtime risks
- Only flag HIGH risk for changes that ACTUALLY affect the user's code
"""

RISK_USER_PROMPT = """Analyze the upgrade risk for `{package_name}` from `{current_version}` to `{target_version}`.

## User's Environment
- Python Version: {python_version}
- Project Config: {project_config}

## User's Code Usage
These symbols from the package are used in the codebase:
{usage_context}

## Changelog
{changelog_text}

---
**TASK**: Identify breaking changes that ACTUALLY affect this user.

REMEMBER:
- User is on Python {python_version}
- If package requires >= 3.11 and user has {python_version}, that is COMPATIBLE (not a risk)
- Only mark HIGH risk for API changes that affect symbols the user actually uses
- Build tool changes are NOT runtime risks
"""

RISK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RISK_SYSTEM_PROMPT),
    ("human", RISK_USER_PROMPT),
])


class RiskAssessorAgent(BaseAgent[RiskAssessment]):
    """
    Analyzes changelogs to identify breaking changes and upgrade risks.

    This is the primary risk assessment agent that evaluates API changes,
    behavioral shifts, and compatibility issues.
    """

    name = "risk_assessor"
    description = "Analyzes breaking changes and upgrade risks"

    @property
    def output_schema(self) -> type[RiskAssessment]:
        return RiskAssessment

    def get_prompt(self):
        return RISK_PROMPT
