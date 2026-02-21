# backend/common/llm/tests/test_registry.py
import pytest

from common.llm.registry import LLMProviderRegistry


class DummyProvider:
    """Dummy provider for testing."""

    def ask_question(self, system_prompt, user_message, temperature=0.0):
        return "dummy response"

    def ask_question_with_usage(self, system_prompt, user_message, temperature=0.0):
        return "dummy response", {}


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before each test to avoid pollution."""
    original_providers = LLMProviderRegistry._providers.copy()
    LLMProviderRegistry._providers.clear()
    yield
    LLMProviderRegistry._providers = original_providers


class TestLLMProviderRegistry:

    def test_register_provider(self):
        """Test registering a new provider."""
        LLMProviderRegistry.register("dummy", DummyProvider)
        assert LLMProviderRegistry.is_registered("dummy")

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate provider raises error."""
        LLMProviderRegistry.register("dummy", DummyProvider)

        with pytest.raises(ValueError, match="already registered"):
            LLMProviderRegistry.register("dummy", DummyProvider)

    def test_get_provider_returns_instance(self):
        """Test getting a provider instance."""
        LLMProviderRegistry.register("dummy", DummyProvider)
        provider = LLMProviderRegistry.get("dummy")

        assert isinstance(provider, DummyProvider)

    def test_get_creates_new_instance_each_time(self):
        """Test that get() creates a new instance each time."""
        LLMProviderRegistry.register("dummy", DummyProvider)

        provider1 = LLMProviderRegistry.get("dummy")
        provider2 = LLMProviderRegistry.get("dummy")

        assert provider1 is not provider2  # Different instances

    def test_get_unknown_provider_raises_error(self):
        """Test getting unknown provider raises error with helpful message."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMProviderRegistry.get("nonexistent")

    def test_get_unknown_provider_shows_available(self):
        """Test error message shows available providers."""
        LLMProviderRegistry.register("provider1", DummyProvider)
        LLMProviderRegistry.register("provider2", DummyProvider)

        with pytest.raises(ValueError, match="provider1, provider2"):
            LLMProviderRegistry.get("nonexistent")

    def test_list_available_providers(self):
        """Test listing all registered providers."""
        LLMProviderRegistry.register("provider1", DummyProvider)
        LLMProviderRegistry.register("provider2", DummyProvider)

        available = LLMProviderRegistry.list_available()
        assert available == ["provider1", "provider2"]  # Sorted

    def test_list_available_returns_sorted_list(self):
        """Test that list_available returns sorted list."""
        LLMProviderRegistry.register("zebra", DummyProvider)
        LLMProviderRegistry.register("alpha", DummyProvider)

        available = LLMProviderRegistry.list_available()
        assert available == ["alpha", "zebra"]

    def test_is_registered(self):
        """Test checking if provider is registered."""
        assert not LLMProviderRegistry.is_registered("dummy")

        LLMProviderRegistry.register("dummy", DummyProvider)
        assert LLMProviderRegistry.is_registered("dummy")
