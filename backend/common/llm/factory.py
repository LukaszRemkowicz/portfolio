# backend/translation/factory.py
from django.conf import settings

from common.llm.providers import GPTProvider, MockLLMProvider

from .protocols import LLMProvider


def get_llm_provider() -> LLMProvider:
    """
    Factory function to create LLM provider based on settings.

    Returns:
        LLMProvider: Configured provider instance

    Raises:
        ValueError: If unknown provider backend is specified
    """
    backend = getattr(settings, "LLM_PROVIDER_BACKEND", "gpt")

    if settings.DEBUG:
        return MockLLMProvider()

    if backend == "gpt":
        return GPTProvider()

    # Future providers can be added here by extending this conditional
    # with additional backends and corresponding provider classes.

    raise ValueError(f"Unknown LLM provider backend: {backend}")
