from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from anvil.agent.agents.base import BaseAgent


class SecurityVulnerability(BaseModel):
    """Details about a security vulnerability."""
    cve_id: Optional[str] = Field(None, description="CVE ID if mentioned (e.g., CVE-2024-1234)")
    severity: str = Field(description="'critical', 'high', 'medium', 'low'")
    description: str = Field(description="What the vulnerability is")
    fixed_in_upgrade: bool = Field(description="Whether this upgrade fixes the vulnerability")
    affects_current: bool = Field(description="Whether the current version is affected")


class SecurityAssessment(BaseModel):
    """Security assessment from the SecurityAuditor agent."""
    summary: str = Field(description="Security summary of the upgrade")
    security_score: str = Field(description="'safe', 'improved', 'neutral', 'concerning'")
    vulnerabilities_fixed: List[SecurityVulnerability] = Field(default_factory=list)
    new_dependencies: List[str] = Field(default_factory=list, description="New transitive dependencies added")
    security_improvements: List[str] = Field(default_factory=list, description="Security enhancements in upgrade")
    security_concerns: List[str] = Field(default_factory=list, description="Any security concerns with upgrading")
    upgrade_recommended: bool = Field(description="Whether upgrade is recommended from security perspective")
    confidence: float = Field(description="Confidence in assessment (0.0-1.0)")


SECURITY_SYSTEM_PROMPT = """You are a Security Engineer specializing in software supply chain security.

Your job: Analyze changelogs for SECURITY IMPLICATIONS of package upgrades.

## What to Look For

1. **Security Fixes**: CVEs, vulnerability patches, security improvements
   - Look for keywords: "security", "CVE", "vulnerability", "fix", "patch", "XSS", "injection", "CSRF"

2. **Security Improvements**: New security features, hardening
   - Input validation improvements
   - Authentication/authorization changes
   - Encryption updates

3. **Security Concerns**: Things that might introduce risk
   - New network calls or external connections
   - Changes to permission models
   - Removed security checks
   - New dependencies (increased attack surface)

4. **Supply Chain**: Dependency changes
   - New dependencies added
   - Dependencies removed
   - Version constraints changed

## Assessment Guidelines

- `safe`: No security concerns, stable upgrade
- `improved`: Upgrade fixes vulnerabilities or adds security features (RECOMMENDED)
- `neutral`: No significant security impact either way
- `concerning`: Potential security concerns that need review

## IMPORTANT: What is NOT a Security Concern

- Build tool updates (cibuildwheel, setuptools, wheel) - these don't affect runtime
- Dev dependency updates - these don't ship with the package
- Test framework updates - these don't affect production code
- Documentation changes - no security impact

Only flag RUNTIME dependencies and actual CVEs as security concerns.
"""

SECURITY_USER_PROMPT = """Analyze the security implications of upgrading `{package_name}` from `{current_version}` to `{target_version}`.

## Environment Context
- Python Version: {python_version}
- Project Config: {project_config}

## Changelog
{changelog_text}

---
**TASK**: Identify all security-relevant changes. Flag any CVEs, security fixes, or concerns.
"""

SECURITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECURITY_SYSTEM_PROMPT),
    ("human", SECURITY_USER_PROMPT),
])


class SecurityAuditorAgent(BaseAgent[SecurityAssessment]):
    """
    Analyzes changelogs for security implications.

    Looks for CVEs, vulnerability fixes, security improvements,
    and potential security concerns in package upgrades.
    """

    name = "security_auditor"
    description = "Analyzes security implications of upgrades"

    @property
    def output_schema(self) -> type[SecurityAssessment]:
        return SecurityAssessment

    def get_prompt(self):
        return SECURITY_PROMPT
