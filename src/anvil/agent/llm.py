from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
# defaulting to ChatOpenAI as a placeholder, but could be dynamic
from langchain_openai import ChatOpenAI 
import os

def get_llm(model_name: str = "gpt-4o", temperature: float = 0.0) -> BaseChatModel:
    """
    Factory to get the LLM instance.
    Currently defaults to OpenAI, but can be extended for Anthropic, Ollama, etc.
    """
    # Check for API key presence or other config
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback or error? For now, let's assume OpenAI or compatible
        pass
        
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key or "sk-placeholder" # placeholder to avoid init crash if just testing
    )
