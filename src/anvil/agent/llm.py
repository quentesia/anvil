from typing import Optional
import os
from langchain_core.language_models.chat_models import BaseChatModel
from anvil.core.logging import get_logger

logger = get_logger("agent.llm")

def get_llm() -> Optional[BaseChatModel]:
    """
    Factory to return the configured ChatModel.
    Defaults to Ollama (llama3) if not specified.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    # User listens on 11434 with qwen2.5-coder:14b
    model_name = os.getenv("LLM_MODEL", "qwen2.5-coder:14b")
    
    logger.debug(f"Initializing LLM: {provider}/{model_name}")

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
            # Configure context length (default 32k for better changelog analysis)
            num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
            logger.debug(f"Ollama context length: {num_ctx}")
            return ChatOllama(model=model_name, temperature=0.0, num_ctx=num_ctx)
        except ImportError:
            logger.error("langchain_ollama not installed. Run `pip install langchain-ollama`.")
            return None
            
    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=0.0)
        except ImportError:
             logger.error("langchain_openai not installed.")
             return None
             
    elif provider == "anthropic":
        # Placeholder for future expansion
        logger.error("Anthropic provider not yet implemented.")
        return None
        
    else:
        logger.error(f"Unknown LLM provider: {provider}")
        return None
