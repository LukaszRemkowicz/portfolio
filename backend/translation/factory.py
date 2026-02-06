# backend/translation/factory.py
from typing import cast

from django.conf import settings

from .providers import LLMProvider


def get_llm_provider() -> LLMProvider:
    """
    Factory function to create LLM provider based on settings.

    Returns:
        LLMProvider: Configured provider instance

    Raises:
        ValueError: If unknown provider backend is specified
    """
    backend = getattr(settings, "LLM_PROVIDER_BACKEND", "gpt")

    if backend == "gpt":
        from .providers import GPTProvider  # noqa: F811

        return cast("GPTProvider", GPTProvider())
    # Future providers can be added here:
    # elif backend == "gemini":
    #     from .providers import GeminiProvider
    #     return GeminiProvider()

    raise ValueError(f"Unknown LLM provider backend: {backend}")
