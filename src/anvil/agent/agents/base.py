import os
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel
from anvil.agent.llm import get_llm
from anvil.core.logging import get_logger

T = TypeVar('T', bound=BaseModel)

logger = get_logger("agent.base")


class AgentContext(BaseModel):
    """Context provided to all agents for analysis."""
    package_name: str
    current_version: str
    target_version: str
    changelog: str
    usage_context: list[str] = []
    python_version: str = "3.x"
    project_config: str = ""


class BaseAgent(ABC, Generic[T]):
    """
    Base class for all AI agents in the multi-agent system.

    Each agent specializes in a specific type of analysis and returns
    a structured assessment. Agents can run in parallel.
    """

    name: str = "base"
    description: str = "Base agent"

    def __init__(self):
        self.llm = get_llm()

    @property
    @abstractmethod
    def output_schema(self) -> type[T]:
        """Pydantic model for the agent's structured output."""
        pass

    @abstractmethod
    def get_prompt(self) -> Any:
        """Returns the ChatPromptTemplate for this agent."""
        pass

    def analyze(self, context: AgentContext) -> Optional[T]:
        """
        Run the agent's analysis on the given context.

        Returns structured output based on the agent's output_schema.
        """
        if not self.llm:
            logger.warning(f"[{self.name}] No LLM configured. Skipping.")
            return None

        logger.info(f"🤖 [{self.name}] Analyzing {context.package_name}...")

        try:
            # Setup structured output
            structured_llm = self.llm.with_structured_output(self.output_schema)
            chain = self.get_prompt() | structured_llm

            # Truncate changelog if needed
            # ~4 chars per token, 32k context = ~25k chars safe for changelog
            changelog = context.changelog
            MAX_CHARS = int(os.environ.get("ANVIL_MAX_CHANGELOG_CHARS", "25000"))
            if len(changelog) > MAX_CHARS:
                logger.warning(f"[{self.name}] Truncating changelog ({len(changelog)} -> {MAX_CHARS} chars)")
                changelog = changelog[:MAX_CHARS] + "\n\n...(truncated)..."

            # Build input dict
            input_dict = {
                "package_name": context.package_name,
                "current_version": context.current_version,
                "target_version": context.target_version,
                "changelog_text": changelog,
                "usage_context": "\n".join(f"- {u}" for u in context.usage_context) or "(No usage found)",
                "python_version": context.python_version,
                "project_config": context.project_config or "(No config available)",
            }

            result = chain.invoke(input_dict)
            logger.info(f"✅ [{self.name}] Analysis complete")
            return result

        except Exception as e:
            logger.error(f"❌ [{self.name}] Analysis failed: {e}")
            return None

    async def analyze_async(self, context: AgentContext) -> Optional[T]:
        """
        Async version of analyze for parallel execution.
        """
        if not self.llm:
            logger.warning(f"[{self.name}] No LLM configured. Skipping.")
            return None

        logger.info(f"🤖 [{self.name}] Analyzing {context.package_name} (async)...")

        try:
            structured_llm = self.llm.with_structured_output(self.output_schema)
            chain = self.get_prompt() | structured_llm

            changelog = context.changelog
            MAX_CHARS = int(os.environ.get("ANVIL_MAX_CHANGELOG_CHARS", "25000"))
            if len(changelog) > MAX_CHARS:
                changelog = changelog[:MAX_CHARS] + "\n\n...(truncated)..."

            input_dict = {
                "package_name": context.package_name,
                "current_version": context.current_version,
                "target_version": context.target_version,
                "changelog_text": changelog,
                "usage_context": "\n".join(f"- {u}" for u in context.usage_context) or "(No usage found)",
                "python_version": context.python_version,
                "project_config": context.project_config or "(No config available)",
            }

            result = await chain.ainvoke(input_dict)
            logger.info(f"✅ [{self.name}] Analysis complete (async)")
            return result

        except Exception as e:
            logger.error(f"❌ [{self.name}] Analysis failed: {e}")
            return None
