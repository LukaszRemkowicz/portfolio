from unittest.mock import patch

from django.test import TransactionTestCase

from astrophotography.models import Tag
from core.services import TranslationService


class TagRefactorTest(TransactionTestCase):
    # setUp removed to rely on standard test runner and avoid IrreversibleError

    def test_tag_creation_generates_slug(self):
        tag = Tag.objects.create(name="Deep Sky")
        self.assertEqual(tag.slug, "deep-sky")

    def test_tag_translation_access(self):
        """
        Verify correct translation behavior for the 'title' field.
        """
        tag = Tag.objects.create(title="Stars")

        # Add Polish translation
        tag.set_current_language("pl")
        tag.title = "Gwiazdy"
        tag.save()

        # Verify English
        tag.set_current_language("en")
        self.assertEqual(tag.title, "Stars")
        self.assertEqual(tag.name, "Stars")  # name should be synced to default lang

        # Verify Polish
        tag.set_current_language("pl")
        self.assertEqual(tag.title, "Gwiazdy")
        self.assertEqual(tag.name, "Stars")  # name column remains canonical (English)

        # Verify direct getter
        self.assertEqual(tag.safe_translation_getter("title", language_code="en"), "Stars")
        self.assertEqual(tag.safe_translation_getter("title", language_code="pl"), "Gwiazdy")

    def test_translation_service_integration(self):
        """
        Verify TranslationService.translate_parler_tag works with the new field structure.
        """
        tag = Tag.objects.create(title="Nebula")

        # Mock the agent to avoid actual GPT calls
        with patch.object(TranslationService.agent, "translate_tag") as mock_translate:
            # Setup mock return
            mock_translate.return_value = "Mgławica"
            mock_translate.__name__ = "mock_translate"

            # Execute service method
            TranslationService.translate_parler_tag(tag, "pl")

            # Verify mock call
            mock_translate.assert_called_with("Nebula", "pl")

            # Verify result in DB
            tag.refresh_from_db()
            saved_title = tag.safe_translation_getter("title", language_code="pl")
            self.assertEqual(saved_title, "Mgławica")
            self.assertEqual(tag.name, "Nebula")  # name column remains canonical (English)
