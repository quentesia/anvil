import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor

from anvil.agent.agents.base import AgentContext
from anvil.agent.agents.risk_assessor import RiskAssessorAgent, RiskAssessment
from anvil.agent.agents.security_auditor import SecurityAuditorAgent, SecurityAssessment
from anvil.agent.agents.compatibility import CompatibilityAgent, CompatibilityAssessment
from anvil.core.models import RiskLevel
from anvil.core.logging import get_logger

logger = get_logger("agent.orchestrator")


class MultiAgentAssessment(BaseModel):
    """Combined assessment from all agents."""
    # Individual assessments
    risk: Optional[RiskAssessment] = None
    security: Optional[SecurityAssessment] = None
    compatibility: Optional[CompatibilityAssessment] = None

    # Aggregated results
    overall_risk: RiskLevel = Field(default=RiskLevel.MEDIUM)
    overall_summary: str = Field(default="")
    upgrade_recommended: bool = Field(default=False)
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)

    # Metadata
    agents_succeeded: List[str] = Field(default_factory=list)
    agents_failed: List[str] = Field(default_factory=list)


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents to analyze package upgrades.

    Runs agents in parallel and aggregates their results into a
    unified assessment with an overall recommendation.
    """

    def __init__(self, parallel: bool = True):
        self.parallel = parallel
        self.agents = [
            RiskAssessorAgent(),
            SecurityAuditorAgent(),
            CompatibilityAgent(),
        ]

    def analyze(self, context: AgentContext) -> MultiAgentAssessment:
        """
        Run all agents and aggregate results.

        Args:
            context: AgentContext with package info and changelog

        Returns:
            MultiAgentAssessment with combined results from all agents
        """
        logger.info(f"🎯 Orchestrating multi-agent analysis for {context.package_name}")
        logger.info(f"   Running {len(self.agents)} agents {'in parallel' if self.parallel else 'sequentially'}")

        if self.parallel:
            results = self._run_parallel(context)
        else:
            results = self._run_sequential(context)

        return self._aggregate(results, context)

    def _run_sequential(self, context: AgentContext) -> dict:
        """Run agents sequentially."""
        results = {}
        for agent in self.agents:
            try:
                result = agent.analyze(context)
                results[agent.name] = result
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                results[agent.name] = None
        return results

    def _run_parallel(self, context: AgentContext) -> dict:
        """Run agents in parallel using ThreadPoolExecutor."""
        results = {}

        def run_agent(agent):
            try:
                return agent.name, agent.analyze(context)
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                return agent.name, None

        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = [executor.submit(run_agent, agent) for agent in self.agents]
            for future in futures:
                name, result = future.result()
                results[name] = result

        return results

    async def analyze_async(self, context: AgentContext) -> MultiAgentAssessment:
        """
        Async version - run all agents concurrently.
        """
        logger.info(f"🎯 Orchestrating async multi-agent analysis for {context.package_name}")

        tasks = [agent.analyze_async(context) for agent in self.agents]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for agent, result in zip(self.agents, results_list):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent.name} failed: {result}")
                results[agent.name] = None
            else:
                results[agent.name] = result

        return self._aggregate(results, context)

    def _aggregate(self, results: dict, context: AgentContext) -> MultiAgentAssessment:
        """Aggregate results from all agents into a unified assessment."""
        assessment = MultiAgentAssessment()

        # Collect individual assessments
        assessment.risk = results.get("risk_assessor")
        assessment.security = results.get("security_auditor")
        assessment.compatibility = results.get("compatibility")

        # Track which agents succeeded
        for name, result in results.items():
            if result is not None:
                assessment.agents_succeeded.append(name)
            else:
                assessment.agents_failed.append(name)

        # Aggregate blocking issues
        blocking = []
        warnings = []
        improvements = []

        # From risk assessment
        if assessment.risk:
            if assessment.risk.risk_level == RiskLevel.HIGH:
                blocking.append(f"High risk: {assessment.risk.summary}")
            elif assessment.risk.risk_level == RiskLevel.MEDIUM:
                warnings.append(f"Medium risk: {assessment.risk.summary}")

            for bc in assessment.risk.breaking_changes:
                if bc.severity == "critical":
                    blocking.append(f"Breaking: {bc.description}")
                else:
                    warnings.append(f"Breaking ({bc.severity}): {bc.description}")

        # From security assessment
        if assessment.security:
            if assessment.security.security_score == "improved":
                improvements.append(f"Security improved: {assessment.security.summary}")
            elif assessment.security.security_score == "concerning":
                warnings.append(f"Security concern: {assessment.security.summary}")

            for vuln in assessment.security.vulnerabilities_fixed:
                if vuln.fixed_in_upgrade and vuln.affects_current:
                    improvements.append(f"Fixes {vuln.cve_id or 'vulnerability'}: {vuln.description}")

            for concern in assessment.security.security_concerns:
                warnings.append(f"Security: {concern}")

        # From compatibility assessment
        if assessment.compatibility:
            if not assessment.compatibility.compatible:
                blocking.append(f"Incompatible: {assessment.compatibility.summary}")
            if not assessment.compatibility.python_compatible:
                blocking.append(f"Python {context.python_version} not supported")

            for issue in assessment.compatibility.issues:
                if issue.severity == "blocking":
                    blocking.append(f"Compatibility: {issue.description}")
                else:
                    warnings.append(f"Compatibility ({issue.severity}): {issue.description}")

        assessment.blocking_issues = blocking
        assessment.warnings = warnings
        assessment.improvements = improvements

        # Determine overall risk level
        assessment.overall_risk = self._calculate_overall_risk(assessment)

        # Determine if upgrade is recommended
        assessment.upgrade_recommended = self._should_recommend(assessment)

        # Generate summary
        assessment.overall_summary = self._generate_summary(assessment, context)

        return assessment

    def _calculate_overall_risk(self, assessment: MultiAgentAssessment) -> RiskLevel:
        """Calculate overall risk from all agent assessments."""
        # If any blocking issues, it's HIGH
        if assessment.blocking_issues:
            return RiskLevel.HIGH

        # Collect risk levels from agents
        risk_levels = []

        if assessment.risk:
            risk_levels.append(assessment.risk.risk_level)

        if assessment.compatibility and not assessment.compatibility.compatible:
            risk_levels.append(RiskLevel.HIGH)

        if assessment.security:
            if assessment.security.security_score == "concerning":
                risk_levels.append(RiskLevel.MEDIUM)
            elif assessment.security.security_score == "improved":
                risk_levels.append(RiskLevel.POSITIVE)

        # Return highest risk, or default to MEDIUM if no data
        if not risk_levels:
            return RiskLevel.MEDIUM

        risk_order = [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.POSITIVE]
        for level in risk_order:
            if level in risk_levels:
                return level

        return RiskLevel.MEDIUM

    def _should_recommend(self, assessment: MultiAgentAssessment) -> bool:
        """Determine if the upgrade should be recommended."""
        # Don't recommend if blocking issues
        if assessment.blocking_issues:
            return False

        # Don't recommend if HIGH risk
        if assessment.overall_risk == RiskLevel.HIGH:
            return False

        # Recommend if security is improved
        if assessment.security and assessment.security.upgrade_recommended:
            return True

        # Recommend if risk is low/positive and compatible
        if assessment.overall_risk in [RiskLevel.LOW, RiskLevel.POSITIVE]:
            if assessment.compatibility and assessment.compatibility.compatible:
                return True
            elif not assessment.compatibility:  # No compatibility data, assume OK
                return True

        # Medium risk - recommend with caution
        if assessment.overall_risk == RiskLevel.MEDIUM:
            return True  # Still recommend, user will see warnings

        return False

    def _generate_summary(self, assessment: MultiAgentAssessment, context: AgentContext) -> str:
        """Generate a human-readable summary."""
        parts = [f"Multi-agent analysis for {context.package_name} {context.current_version} → {context.target_version}:"]

        if assessment.improvements:
            parts.append(f"✅ {len(assessment.improvements)} improvement(s)")
        if assessment.warnings:
            parts.append(f"⚠️ {len(assessment.warnings)} warning(s)")
        if assessment.blocking_issues:
            parts.append(f"🛑 {len(assessment.blocking_issues)} blocking issue(s)")

        if assessment.upgrade_recommended:
            parts.append("→ Upgrade RECOMMENDED")
        else:
            parts.append("→ Review required before upgrade")

        return " | ".join(parts)
