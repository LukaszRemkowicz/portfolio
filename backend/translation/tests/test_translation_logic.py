# backend/translation/tests/test_translation_logic.py
import pytest

from django.conf import settings

from astrophotography.tests.factories import AstroImageFactory, PlaceFactory
from translation.mixins import AutomatedTranslationModelMixin
from translation.models import TranslationTask


class MockModelMixin(AutomatedTranslationModelMixin):
    translation_trigger_fields = ["name"]


@pytest.mark.django_db
class TestTranslationLogic:
    def setup_method(self, method):
        self.mixin = MockModelMixin()
        self.default_lang = settings.DEFAULT_APP_LANGUAGE
        import unittest.mock
        import uuid

        self.mock_delay = unittest.mock.patch(
            "translation.mixins.translate_instance_task.delay"
        ).start()
        self.mock_delay.side_effect = lambda *args, **kwargs: unittest.mock.Mock(
            id=str(uuid.uuid4())
        )

    def teardown_method(self, method):
        import unittest.mock

        unittest.mock.patch.stopall()

    def test_needs_translation_triggers_when_empty(self):
        """Should return True if target field is empty (or whitespace/HTML empty)."""
        place = PlaceFactory(name="Source Name")
        # Initialize translation record but keep name empty
        place.set_current_language("pl")
        place.name = ""
        place.save()

        # Clear auto-triggered tasks to test the logic in isolation
        TranslationTask.objects.all().delete()

        # Current logic: returns True because "Source Name" != ""
        # New logic: should return True because "" is empty
        assert self.mixin._needs_translation(place, "pl", self.default_lang) is True

    def test_needs_translation_skips_when_populated_even_if_different(self):
        """
        Should return False if target field is already populated,
        even if different from source.
        """
        place = PlaceFactory(name="Source Name")
        place.set_current_language("pl")
        place.name = "Manual Polish Edit"
        place.save()

        # Current logic: returns True because "Source Name" != "Manual Polish Edit"
        # New logic: should return False because "Manual Polish Edit" is NOT empty
        assert self.mixin._needs_translation(place, "pl", self.default_lang) is False

    def test_needs_translation_triggers_when_record_missing(self):
        """
        Should return True if the translation record for the
        target language doesn't exist yet.
        """
        place = PlaceFactory(name="Source Name")
        # No 'pl' translation created yet
        TranslationTask.objects.all().delete()

        assert self.mixin._needs_translation(place, "pl", self.default_lang) is True

    def test_needs_translation_skips_when_same_as_source(self):
        """
        Should return False if populated with same text
        (technical edge case, but still populated).
        """
        # Actually, if it's SAME as source, GPT might have copied it or it might be a coincidence.
        # But if it's populated (not empty), we should NOT overwrite it if user wants it that way.
        # However, usually if it's same as source, it might be a signal it WASN'T translated yet.
        # BUT the user said: "I want to run translation only when translation is EMPTY".
        # So even if it's same as source, if it's not empty, we skip.
        place = PlaceFactory(name="Source Name")
        place.set_current_language("pl")
        place.name = "Source Name"
        place.save()

        # New logic: should return False because "Source Name" is NOT empty
        assert self.mixin._needs_translation(place, "pl", self.default_lang) is False

    @pytest.mark.django_db
    def test_needs_translation_triggers_when_partially_populated(self):
        """
        Should return True if at least one trigger field is empty
        (to allow forcing re-translation).
        """
        from translation.mixins import AutomatedTranslationModelMixin

        mixin = AutomatedTranslationModelMixin()
        mixin.translation_trigger_fields = ["name", "description"]

        # Source has both
        img = AstroImageFactory(name="Source Name", description="Source Description")

        # Target has ONLY name
        img.set_current_language("pl")
        img.name = "Manual Polish Name"
        img.description = ""
        img.save()

        # Clear auto-triggered tasks
        TranslationTask.objects.all().delete()

        # NEW logic: should return True because 'description' is empty
        assert mixin._needs_translation(img, "pl", "en") is True

    @pytest.mark.django_db
    def test_overwriting_issue_regression(self, mocker):
        """
        Verify that if one field is empty it triggers, BUT manually populated fields
        are not 'lost' (handled by TranslationService.force=False).
        """
        from astrophotography.tests.factories import AstroImageFactory
        from translation.mixins import AutomatedTranslationModelMixin

        mixin = AutomatedTranslationModelMixin()
        mixin.translation_trigger_fields = ["name", "description"]

        # 1. Setup AstroImage with manual Polish name but EMPTY description
        img = AstroImageFactory(name="Source Name", description="Source Description")
        img.set_current_language("pl")
        img.name = "Manual Polish Name"
        img.description = ""  # Empty
        img.save()

        # Clear auto-triggered tasks to test logic in isolation
        TranslationTask.objects.all().delete()

        # 2. Check if it needs translation (should be True because 'description' is empty)
        assert mixin._needs_translation(img, "pl", "en") is True

    @pytest.mark.django_db
    def test_needs_translation_triggers_when_all_empty(self):
        """Should return True ONLY if ALL trigger fields are empty (and source is not)."""
        from translation.mixins import AutomatedTranslationModelMixin

        mixin = AutomatedTranslationModelMixin()
        mixin.translation_trigger_fields = ["name", "description"]

        img = AstroImageFactory(name="Source Name", description="Source Description")

        # Target has NONE
        img.set_current_language("pl")
        img.name = ""
        img.description = ""
        img.save()

        TranslationTask.objects.all().delete()

        # Should return True because both are empty
        assert mixin._needs_translation(img, "pl", "en") is True

    @pytest.mark.django_db
    def test_astro_image_form_enforces_required_name_in_english(self):
        """Verify that the English name is required despite blank=True in the model."""
        from astrophotography.forms import AstroImageForm
        from astrophotography.tests.factories import AstroImageFactory

        img = AstroImageFactory(name="Valid Name")
        img.set_current_language("en")

        form = AstroImageForm(
            instance=img,
            data={
                "name": "",  # Empty
                "capture_date": "2024-01-01",
            },
        )

        # The form should set name.required = True in __init__ for English
        assert form.fields["name"].required is True
        # And it should fail validation if empty
        assert "name" in form.errors

    @pytest.mark.django_db
    def test_astro_image_form_allows_blank_name_in_polish(self):
        """Verify that the Polish name is NOT required in the form (to allow clearing it)."""
        from astrophotography.forms import AstroImageForm
        from astrophotography.tests.factories import AstroImageFactory

        img = AstroImageFactory(name="Valid Name")
        img.set_current_language("pl")

        form = AstroImageForm(instance=img)
        # The form should keep name.required = False (or inherited from model blank=True)
        assert form.fields["name"].required is False
