# backend/core/tests/test_translation_service.py
import pytest

from django.conf import settings

from core.services import TranslationService


@pytest.mark.django_db
class TestTranslationService:
    def test_get_available_languages_returns_list(self):
        """
        Verify that get_available_languages returns a list of language codes.
        """
        languages = TranslationService.get_available_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        # In this project, expected languages are 'en' and 'pl'
        assert "en" in languages
        assert "pl" in languages

    @pytest.mark.django_db
    def test_get_available_languages_matches_settings(self):
        """
        Verify that the returned languages match what's configured in PARLER_LANGUAGES.
        """
        languages = TranslationService.get_available_languages()

        # Parler global settings are stored under the None key
        parler_configs = getattr(settings, "PARLER_LANGUAGES", {})
        parler_langs = parler_configs.get(None, [])

        expected_codes = [
            lang["code"] for lang in parler_langs if isinstance(lang, dict) and "code" in lang
        ]

        # Ensure we found some expected codes to compare against
        assert len(expected_codes) > 0
        assert set(languages) == set(expected_codes)

    def test_fetch_place_name_calls_agent_correctly(self):
        """
        Verify that TranslationService.fetch_place_name calls GPTTranslationAgent
        with the correct argument order (source_text, language_code, country).
        """
        from unittest.mock import patch

        # Mock the agent's instance
        with patch("core.services.GPTTranslationAgent") as mock_agent_class:
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.translate_place.return_value = "Hawaje"

            service = TranslationService()
            result = service.fetch_place_name("Hawaii", "US", "pl")

            assert result == "Hawaje"

            # CRITICAL CHECK: Verified the argument order:
            # translate_place(text, target_lang_code, country_name)
            mock_agent_instance.translate_place.assert_called_once_with("Hawaii", "pl", "US")
