import structlog
from app.config.settings import settings
from app.llm.providers import BaseLLMProvider, MockProvider, OpenAIProvider

logger = structlog.get_logger("aegis.llm")

from typing import AsyncGenerator

class LLMClient:
    """Entry point resolving configurations to initialize the active LLM provider."""
    
    _provider: BaseLLMProvider | None = None
    
    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        """Resolves configuration and instantiates the selected provider singleton."""
        if cls._provider is None:
            provider_name = settings.LLM_PROVIDER.lower()
            logger.info("Initializing LLM Provider", provider=provider_name)
            
            if provider_name == "mock":
                cls._provider = MockProvider()
            elif provider_name == "openai":
                cls._provider = OpenAIProvider()
            else:
                logger.error("invalid_llm_provider_configured", provider=provider_name)
                raise ValueError(f"Unsupported LLM provider: {provider_name}")
                
        return cls._provider
        
    @classmethod
    def generate(cls, prompt: str) -> str:
        """Generates text completions through the active provider backend."""
        provider = cls.get_provider()
        return provider.generate_text(prompt)

    @classmethod
    async def generate_stream(cls, prompt: str) -> AsyncGenerator[str, None]:
        """Generates text stream chunks through the active provider backend."""
        provider = cls.get_provider()
        async for chunk in provider.generate_text_stream(prompt):
            yield chunk

