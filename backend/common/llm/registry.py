# backend/common/llm/registry.py
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .protocols import LLMProvider

logger = logging.getLogger(__name__)


class LLMProviderRegistry:
    """
    Global registry for LLM providers.

    Providers self-register by calling register() at module import time.
    This follows the Open/Closed Principle - new providers can be added
    without modifying existing code.

    Usage:
        # Register a provider (done in provider module)
        LLMProviderRegistry.register("gpt", GPTProvider)

        # Get a provider instance
        provider = LLMProviderRegistry.get("gpt")

        # List available providers
        providers = LLMProviderRegistry.list_available()
    """

    _providers: dict[str, type["LLMProvider"]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type["LLMProvider"]) -> None:
        """
        Register a provider class.

        Called automatically when provider modules are imported.

        Args:
            name: Provider name (e.g., "gpt", "gemini", "claude")
            provider_class: Provider class to register

        Raises:
            ValueError: If provider name is already registered
        """
        if name in cls._providers:
            raise ValueError(
                f"Provider '{name}' is already registered. "
                f"Existing: {cls._providers[name].__name__}, "
                f"New: {provider_class.__name__}"
            )

        cls._providers[name] = provider_class
        logger.info("Registered LLM provider: %s -> %s", name, provider_class.__name__)

    @classmethod
    def get(cls, name: str) -> "LLMProvider":
        """
        Get an instance of a registered provider.

        Args:
            name: Provider name

        Returns:
            New instance of the provider

        Raises:
            ValueError: If provider is not registered
        """
        provider_class = cls._providers.get(name)

        if not provider_class:
            available = ", ".join(sorted(cls._providers.keys()))
            raise ValueError(
                f"Unknown LLM provider: '{name}'. " f"Available providers: {available or 'none'}"
            )

        return provider_class()

    @classmethod
    def list_available(cls) -> list[str]:
        """
        List all registered provider names.

        Returns:
            Sorted list of provider names
        """
        return sorted(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._providers
