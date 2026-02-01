from unittest.mock import MagicMock

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

    def test_get_translated_field_generates_stub_when_missing(self):
        from core.services import TranslationService

        instance = MagicMock()
        instance.title = "Original Title"
        instance.translations = {}

        result = TranslationService.get_translated_field(instance, "title", "pl")

        expected_stub = "[TRANSLATED to pl] Original Title"
        assert result == expected_stub

        # Verify it updated the instance.translations
        assert instance.translations["pl"]["title"] == expected_stub
        # Verify it saved
        instance.save.assert_called_once_with(update_fields=["translations"])
