# backend/core/tests/test_translation_service.py
from unittest.mock import MagicMock, patch

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
        with patch.object(TranslationService.agent, "translate_place") as mock_translate:
            mock_translate.return_value = "Hawaje"

            result = TranslationService.fetch_place_name("Hawaii", "US", "pl")

            assert result == "Hawaje"
            mock_translate.assert_called_once_with("Hawaii", "pl", "US")

    def test_is_empty_text_edge_cases(self):
        """
        Verify is_empty_text with various HTML and whitespace edge cases.
        """
        assert TranslationService.is_empty_text("") is True
        assert TranslationService.is_empty_text(None) is True
        assert TranslationService.is_empty_text("<p></p>") is True
        assert TranslationService.is_empty_text("<p>&nbsp;</p>") is True
        assert TranslationService.is_empty_text("   ") is True
        assert TranslationService.is_empty_text("<p>Content</p>") is False
        assert TranslationService.is_empty_text("Valid") is False

    @pytest.mark.django_db
    def test_parler_ceremony_skip_if_exists(self):
        """
        Verify that _parler_ceremony yields None and stops if translation exists.
        """
        instance = MagicMock()

        # Scenario: Translation already exists
        with patch.object(TranslationService, "_has_translation", return_value=(True, "Existing")):
            gen = TranslationService._parler_ceremony(instance, "name", "pl")
            val = next(gen)
            assert val is None
            with pytest.raises(StopIteration):
                next(gen)

    @pytest.mark.django_db
    def test_parler_ceremony_yields_source(self):
        """
        Verify that _parler_ceremony yields source text if translation is missing.
        """
        instance = MagicMock()
        instance.get_current_language.return_value = "en"

        with patch.object(TranslationService, "_has_translation", return_value=(False, None)):
            with patch.object(
                TranslationService, "_get_default_language_text", return_value="Source"
            ):
                gen = TranslationService._parler_ceremony(instance, "name", "pl")
                val = next(gen)
                assert val == "Source"

                # Send back the translation
                try:
                    gen.send("Translated")
                except StopIteration:
                    pass

                # Verify instance was updated
                instance.set_current_language.assert_any_call("pl")
                instance.set_current_language.assert_any_call("en")

    def test_translate_parler_tag_uses_correct_agent_method(self):
        """
        Verify that translate_parler_tag calls translate_tag and handles slugs.
        """
        instance = MagicMock()
        instance.get_current_language.return_value = "en"
        instance.name = "TranslatedTag"

        with patch.object(TranslationService, "_has_translation", return_value=(False, None)):
            with patch.object(
                TranslationService, "_get_default_language_text", return_value="Source"
            ):
                with patch.object(
                    TranslationService.agent, "translate_tag", return_value="TranslatedTag"
                ) as mock_translate:
                    result = TranslationService.translate_parler_tag(instance, "pl")

                    assert result == ["TranslatedTag", "translatedtag"]
                    mock_translate.assert_called_once_with("Source", "pl")
                    assert instance.name == "TranslatedTag"
                    assert instance.slug == "translatedtag"

    def test_translate_astro_image_uses_html_agent_for_description(self):
        """
        Verify that translate_astro_image correctly uses HTML agent for description
        and standard agent for others.
        """
        instance = MagicMock()

        # We want to track which handlers were passed to _run_parler_translation
        with patch.object(TranslationService, "_run_parler_translation") as mock_run:
            TranslationService.translate_astro_image(instance, "pl")

            # Check calls
            # fields = ["name", "description", "exposure_details", "processing_details"]
            call_args_list = mock_run.call_args_list
            assert len(call_args_list) == 4

            # Index 1 is description
            handler_description = call_args_list[1][0][3]
            assert handler_description == TranslationService.agent.translate_html

            # Index 0 is name
            handler_name = call_args_list[0][0][3]
            assert handler_name == TranslationService.agent.translate

    @pytest.mark.django_db
    def test_parler_ceremony_obeys_force_parameter(self):
        """
        Verify that _parler_ceremony yields source text even if translation exists
        when force=True is passed.
        """
        instance = MagicMock()
        instance.get_current_language.return_value = "en"

        # When force=True, _has_translation(..., force=True) returns (False, None)
        # which triggers the ceremony to yield source
        with patch.object(TranslationService, "_get_default_language_text", return_value="Source"):
            gen = TranslationService._parler_ceremony(instance, "name", "pl", force=True)
            val = next(gen)
            assert val == "Source"
