"""
Tests for the multi-agent system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from anvil.agent.agents import (
    AgentContext,
    AgentOrchestrator,
    RiskAssessorAgent,
    SecurityAuditorAgent,
    CompatibilityAgent,
    MultiAgentAssessment,
)
from anvil.agent.agents.risk_assessor import RiskAssessment
from anvil.agent.agents.security_auditor import SecurityAssessment
from anvil.agent.agents.compatibility import CompatibilityAssessment
from anvil.core.models import RiskLevel


class TestAgentContext:
    """Test AgentContext creation and validation."""

    def test_create_context(self):
        """Test creating an agent context with all fields."""
        context = AgentContext(
            package_name="requests",
            current_version="2.28.0",
            target_version="2.31.0",
            changelog="## 2.31.0\n- Fixed bug\n- Added feature",
            usage_context=["requests.get", "requests.post"],
            python_version="3.11.0",
            project_config="[project]\nname = 'test'"
        )

        assert context.package_name == "requests"
        assert context.current_version == "2.28.0"
        assert context.target_version == "2.31.0"
        assert "Fixed bug" in context.changelog
        assert len(context.usage_context) == 2
        assert context.python_version == "3.11.0"

    def test_context_defaults(self):
        """Test context with default values."""
        context = AgentContext(
            package_name="test",
            current_version="1.0",
            target_version="2.0",
            changelog="changelog"
        )

        assert context.usage_context == []
        assert context.python_version == "3.x"
        assert context.project_config == ""


class TestRiskAssessorAgent:
    """Test RiskAssessorAgent."""

    def test_agent_properties(self):
        """Test agent has correct properties."""
        agent = RiskAssessorAgent()
        assert agent.name == "risk_assessor"
        assert agent.description == "Analyzes breaking changes and upgrade risks"
        assert agent.output_schema == RiskAssessment

    def test_get_prompt(self):
        """Test prompt is returned."""
        agent = RiskAssessorAgent()
        prompt = agent.get_prompt()
        assert prompt is not None

    @patch('anvil.agent.agents.base.get_llm')
    def test_analyze_no_llm(self, mock_get_llm):
        """Test analyze returns None when no LLM configured."""
        mock_get_llm.return_value = None
        agent = RiskAssessorAgent()

        context = AgentContext(
            package_name="test",
            current_version="1.0",
            target_version="2.0",
            changelog="test changelog"
        )

        result = agent.analyze(context)
        assert result is None


class TestSecurityAuditorAgent:
    """Test SecurityAuditorAgent."""

    def test_agent_properties(self):
        """Test agent has correct properties."""
        agent = SecurityAuditorAgent()
        assert agent.name == "security_auditor"
        assert agent.description == "Analyzes security implications of upgrades"
        assert agent.output_schema == SecurityAssessment

    def test_get_prompt(self):
        """Test prompt is returned."""
        agent = SecurityAuditorAgent()
        prompt = agent.get_prompt()
        assert prompt is not None


class TestCompatibilityAgent:
    """Test CompatibilityAgent."""

    def test_agent_properties(self):
        """Test agent has correct properties."""
        agent = CompatibilityAgent()
        assert agent.name == "compatibility"
        assert agent.description == "Analyzes compatibility and dependency conflicts"
        assert agent.output_schema == CompatibilityAssessment

    def test_get_prompt(self):
        """Test prompt is returned."""
        agent = CompatibilityAgent()
        prompt = agent.get_prompt()
        assert prompt is not None


class TestAgentOrchestrator:
    """Test AgentOrchestrator."""

    def test_orchestrator_init(self):
        """Test orchestrator initializes with agents."""
        orchestrator = AgentOrchestrator(parallel=True)
        assert len(orchestrator.agents) == 3
        assert orchestrator.parallel is True

    def test_orchestrator_sequential_mode(self):
        """Test orchestrator can be set to sequential mode."""
        orchestrator = AgentOrchestrator(parallel=False)
        assert orchestrator.parallel is False

    @patch('anvil.agent.agents.base.get_llm')
    def test_analyze_no_llm(self, mock_get_llm):
        """Test orchestrator handles no LLM gracefully."""
        mock_get_llm.return_value = None
        orchestrator = AgentOrchestrator(parallel=False)

        context = AgentContext(
            package_name="test",
            current_version="1.0",
            target_version="2.0",
            changelog="test changelog"
        )

        result = orchestrator.analyze(context)

        # Should return MultiAgentAssessment with None agents
        assert isinstance(result, MultiAgentAssessment)
        assert result.risk is None
        assert result.security is None
        assert result.compatibility is None
        assert "risk_assessor" in result.agents_failed
        assert "security_auditor" in result.agents_failed
        assert "compatibility" in result.agents_failed


class TestMultiAgentAssessment:
    """Test MultiAgentAssessment aggregation."""

    def test_default_values(self):
        """Test default values for assessment."""
        assessment = MultiAgentAssessment()
        assert assessment.overall_risk == RiskLevel.MEDIUM
        assert assessment.upgrade_recommended is False
        assert assessment.blocking_issues == []
        assert assessment.warnings == []
        assert assessment.improvements == []

    def test_assessment_with_values(self):
        """Test assessment with populated values."""
        assessment = MultiAgentAssessment(
            overall_risk=RiskLevel.LOW,
            upgrade_recommended=True,
            blocking_issues=[],
            warnings=["Minor warning"],
            improvements=["Security fix"],
            agents_succeeded=["risk_assessor", "security_auditor", "compatibility"],
            agents_failed=[]
        )

        assert assessment.overall_risk == RiskLevel.LOW
        assert assessment.upgrade_recommended is True
        assert len(assessment.warnings) == 1
        assert len(assessment.improvements) == 1
        assert len(assessment.agents_succeeded) == 3


class TestOrchestratorAggregation:
    """Test the orchestrator's aggregation logic."""

    def test_calculate_overall_risk_with_blocking(self):
        """Test that blocking issues result in HIGH risk."""
        orchestrator = AgentOrchestrator()

        assessment = MultiAgentAssessment(
            blocking_issues=["Incompatible Python version"]
        )

        risk = orchestrator._calculate_overall_risk(assessment)
        assert risk == RiskLevel.HIGH

    def test_calculate_overall_risk_no_data(self):
        """Test default risk when no agent data."""
        orchestrator = AgentOrchestrator()
        assessment = MultiAgentAssessment()

        risk = orchestrator._calculate_overall_risk(assessment)
        assert risk == RiskLevel.MEDIUM

    def test_should_recommend_with_blocking(self):
        """Test upgrade not recommended when blocking issues exist."""
        orchestrator = AgentOrchestrator()

        assessment = MultiAgentAssessment(
            blocking_issues=["Something is blocking"]
        )

        assert orchestrator._should_recommend(assessment) is False

    def test_should_recommend_high_risk(self):
        """Test upgrade not recommended for high risk."""
        orchestrator = AgentOrchestrator()

        assessment = MultiAgentAssessment(
            overall_risk=RiskLevel.HIGH
        )

        assert orchestrator._should_recommend(assessment) is False

    def test_should_recommend_low_risk(self):
        """Test upgrade recommended for low risk with compatibility."""
        orchestrator = AgentOrchestrator()

        # Create a proper compatibility assessment
        compat = CompatibilityAssessment(
            summary="Compatible",
            compatible=True,
            python_compatible=True,
            issues=[],
            deprecated_features_used=[],
            dependency_changes=[],
            confidence=0.9
        )

        assessment = MultiAgentAssessment(
            overall_risk=RiskLevel.LOW,
            compatibility=compat
        )

        assert orchestrator._should_recommend(assessment) is True


class TestPythonVersionDetection:
    """Test Python version detection for projects."""

    def test_detect_from_python_version_file(self, tmp_path):
        """Test detection from .python-version file."""
        from anvil.agent.nodes.analyze import _detect_project_python_version

        # Create .python-version file
        version_file = tmp_path / ".python-version"
        version_file.write_text("3.12.0")

        detected = _detect_project_python_version(tmp_path)
        assert detected == "3.12.0"

    def test_detect_from_pyproject(self, tmp_path):
        """Test detection from pyproject.toml requires-python."""
        from anvil.agent.nodes.analyze import _detect_project_python_version

        # Create pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"')

        detected = _detect_project_python_version(tmp_path)
        assert detected == "3.11"

    def test_detect_priority(self, tmp_path):
        """Test .python-version takes priority over pyproject.toml."""
        from anvil.agent.nodes.analyze import _detect_project_python_version

        # Create both files
        version_file = tmp_path / ".python-version"
        version_file.write_text("3.13.2")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"')

        detected = _detect_project_python_version(tmp_path)
        assert detected == "3.13.2"  # .python-version takes priority
