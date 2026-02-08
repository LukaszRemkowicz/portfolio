# backend/translation/factory.py
from typing import cast

from django.conf import settings

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

    if backend == "gpt":
        from .providers import GPTProvider  # noqa: F811

        return cast("GPTProvider", GPTProvider())  # type: ignore[redundant-cast]
    # Future providers can be added here by extending this conditional
    # with additional backends and corresponding provider classes.

    raise ValueError(f"Unknown LLM provider backend: {backend}")
