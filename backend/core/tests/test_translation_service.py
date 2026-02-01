from unittest.mock import MagicMock, patch

import pytest

# We will import TranslationService from core.services once implemented
# from core.services import TranslationService

# Placeholder for now until service is created, but we write the test assuming it exists.
# Since we can't import it yet, I will define a fixture that *will* import it or fail if not found,
# but practically in TDD I should write the test that fails to import or fails to run.


class TestTranslationService:
    def test_import_service(self):
        """Simple test to verify service exists (will fail first)"""
        try:
            from core.services import TranslationService

            assert TranslationService
        except ImportError:
            pytest.fail("TranslationService not implemented yet")

    def test_get_translated_field_returns_original_for_en(self):
        from core.services import TranslationService

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {}

        result = TranslationService.get_translated_field(instance, "title", "en")
        assert result == "Original Title"
        instance.save.assert_not_called()

    def test_get_translated_field_returns_original_for_none_lang(self):
        from core.services import TranslationService

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {}

        result = TranslationService.get_translated_field(instance, "title", None)
        assert result == "Original Title"

    def test_get_translated_field_returns_existing_translation(self):
        from core.services import TranslationService

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {"pl": {"title": "Tytuł Polski"}}

        result = TranslationService.get_translated_field(instance, "title", "pl")
        assert result == "Tytuł Polski"
        instance.save.assert_not_called()

    @patch("core.ai_agents.GPTTranslationAgent")
    def test_get_translated_field_calls_agent_when_missing(self, mock_agent_cls):
        from core.services import TranslationService

        # Setup Mock Agent
        mock_agent_instance = mock_agent_cls.return_value
        mock_agent_instance.translate.return_value = "AI Translated Text"

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {}

        result = TranslationService.get_translated_field(instance, "title", "pl")

        # Verify result
        assert result == "AI Translated Text"

        # Verify Agent Call
        mock_agent_instance.translate.assert_called_once_with("Original Title", "pl")

        # Verify Save
        assert instance.translations["pl"]["title"] == "AI Translated Text"
        instance.save.assert_called_once_with(update_fields=["translations"])

    @patch("core.ai_agents.GPTTranslationAgent")
    def test_get_translated_field_handles_agent_failure(self, mock_agent_cls):
        from core.services import TranslationService

        # Setup Mock Agent to Fail (return None)
        mock_agent_instance = mock_agent_cls.return_value
        mock_agent_instance.translate.return_value = None

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {}

        result = TranslationService.get_translated_field(instance, "title", "pl")

        # Verify Fallback
        expected_fallback = "[TRANSLATION FAILED] Original Title"
        assert result == expected_fallback

        # Verify Save of Fallback
        assert instance.translations["pl"]["title"] == expected_fallback
        instance.save.assert_called_once_with(update_fields=["translations"])
