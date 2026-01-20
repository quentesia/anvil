from typing import Optional
from langchain_core.output_parsers import PydanticOutputParser
from anvil.agent.llm import get_llm
from anvil.agent.prompts import analysis_prompt
from anvil.core.models import ImpactAssessment, RiskLevel
from anvil.core.logging import get_logger

logger = get_logger("agent.brain")

class RiskAssessor:
    """Uses AI to assess the risk of a dependency upgrade."""
    
    def __init__(self):
        self.llm = get_llm()
        
    
    def assess_changelog(self, package_name: str, current_version: str, target_version: str, changelog_text: str, usage_context: list[str] = None, python_version: str = "3.x", project_config: str = "") -> Optional[ImpactAssessment]:
        if not self.llm:
            logger.warning("No LLM configured. Skipping AI analysis.")
            return None
        
        usage_str = "\n".join(f"- {u}" for u in (usage_context or []))
        if not usage_str:
            usage_str = "(No direct usage found in codebase)"
            
        logger.info(f"🧠 AI analyzing risk for {package_name} ({current_version}->{target_version})...")
        
        try:
            # Setup structured output
            structured_llm = self.llm.with_structured_output(ImpactAssessment)
            
            chain = analysis_prompt | structured_llm
            
            # --- CONTEXT SAFETY ---
            # Truncate massive changelogs to prevent context window overflow.
            # 20k chars is approx 5k tokens. Safe for 8k-32k models, risky for 2k, but better than crashing.
            MAX_CHARS = 20000
            if len(changelog_text) > MAX_CHARS:
                logger.warning(f"⚠️ Changelog massive ({len(changelog_text)} chars). Truncating to {MAX_CHARS}...")
                changelog_text = changelog_text[:MAX_CHARS] + "\n\n...(Truncated older release notes for analysis safety)..."
            # ----------------------
            
            # --- DEBUG LOGGING ---
            final_prompt_val = analysis_prompt.format(
                package_name=package_name,
                current_version=current_version,
                target_version=target_version,
                changelog_text=changelog_text[:500] + "...", # Truncate for log
                usage_context=usage_str,
                python_version=python_version,
                project_config=project_config
            )
            logger.debug(f"🛑 GENERATED PROMPT SNAPSHOT:\n{final_prompt_val}\n")
            # ---------------------
            
            result = chain.invoke({
                "package_name": package_name,
                "current_version": current_version,
                "target_version": target_version,
                "changelog_text": changelog_text,
                "usage_context": usage_str,
                "python_version": python_version,
                "project_config": project_config
            })
            
            return result
            
        except Exception as e:
            logger.error(f"AI Analysis Failed: {e}")
            return None
