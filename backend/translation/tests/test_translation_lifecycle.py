# backend/translation/tests/test_translation_lifecycle.py
import pytest

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from astrophotography.tests.factories import AstroImageFactory, PlaceFactory, TagFactory
from translation.models import TranslationTask


@pytest.mark.django_db
class TestTranslationLifecycle:
    def setup_method(self):
        self.default_lang = settings.DEFAULT_APP_LANGUAGE
        from translation.services import TranslationService

        supported = TranslationService.get_available_languages()
        self.target_lang = "pl" if "pl" in supported else supported[1]

    def test_creation_queues_translation(self, mocker):
        """1) Create AstroImage -> check translations task exists."""
        # Mock delay to produce unique IDs
        mock_delay = mocker.patch("translation.mixins.translate_instance_task.delay")
        import uuid

        mock_delay.side_effect = lambda *args, **kwargs: mocker.Mock(id=str(uuid.uuid4()))

        # Create image
        img = AstroImageFactory(name="Deep Sky Object")

        # Check if TranslationTask was created
        ct = ContentType.objects.get_for_model(img)
        task = TranslationTask.objects.filter(
            content_type=ct, object_id=str(img.pk), language=self.target_lang
        ).first()

        assert task is not None
        assert task.status == TranslationTask.Status.PENDING
        assert mock_delay.called

    def test_clear_field_re_triggers_translation(self, mocker):
        """3) Clear field in translation, save model -> check if task started."""
        # Mock delay with unique IDs
        mock_delay = mocker.patch("translation.mixins.translate_instance_task.delay")
        import uuid

        mock_delay.side_effect = lambda *args, **kwargs: mocker.Mock(id=str(uuid.uuid4()))

        img = AstroImageFactory(name="Galaxy")
        img.set_current_language(self.target_lang)
        img.name = "Galaktyka"
        img.save()

        # Clear previous tasks
        TranslationTask.objects.all().delete()
        mock_delay.reset_mock()

        # 2. Clear ONLY the name in Polish
        img.set_current_language(self.target_lang)
        img.name = ""
        img.save()

        # 3. Verify task is queued
        ct = ContentType.objects.get_for_model(img)
        assert TranslationTask.objects.filter(
            content_type=ct, object_id=str(img.pk), language=self.target_lang
        ).exists()
        assert mock_delay.called

    def test_required_field_exception(self):
        """4) Remove required fields in these models and try to save() -> rise exception."""
        img = AstroImageFactory.build(name="")

        with pytest.raises(ValidationError) as excinfo:
            img.full_clean()

        assert "name" in excinfo.value.message_dict

    def test_core_field_change_triggers_if_target_empty(self, mocker):
        """5) Core model field value change -> trans is started (if target empty)."""
        # Mock delay with unique IDs
        mock_delay = mocker.patch("translation.mixins.translate_instance_task.delay")
        import uuid

        mock_delay.side_effect = lambda *args, **kwargs: mocker.Mock(id=str(uuid.uuid4()))

        img = AstroImageFactory(name="Old Name")
        # Ensure target is empty
        img.set_current_language(self.target_lang)
        img.name = ""
        img.save()

        TranslationTask.objects.all().delete()
        mock_delay.reset_mock()

        # Change core field
        img.set_current_language(self.default_lang)
        img.name = "New Better Name"
        img.save()

        # Should trigger because target is empty
        assert mock_delay.called

    def test_other_models_lifecycle(self, mocker):
        """Verify Tag and Place also queue translations."""
        mock_delay = mocker.patch("translation.mixins.translate_instance_task.delay")
        import uuid

        mock_delay.side_effect = lambda *args, **kwargs: mocker.Mock(id=str(uuid.uuid4()))

        tag = TagFactory(name="Nebula")
        place = PlaceFactory(name="Tenerife")

        assert TranslationTask.objects.filter(
            object_id=str(tag.pk), language=self.target_lang
        ).exists()
        assert TranslationTask.objects.filter(
            object_id=str(place.pk), language=self.target_lang
        ).exists()

    def test_core_field_change_skips_if_target_populated(self, mocker):
        """
        Verify that changing core field does NOT trigger re-translation
        if target is populated.
        """
        mock_delay = mocker.patch("translation.mixins.translate_instance_task.delay")
        import uuid

        mock_delay.side_effect = lambda *args, **kwargs: mocker.Mock(id=str(uuid.uuid4()))

        img = AstroImageFactory(name="Old Name", description="Old Desc")
        img.set_current_language(self.target_lang)
        img.name = "Manual Name"
        img.description = "Manual Desc"
        img.exposure_details = "Manual Exposure"
        img.processing_details = "Manual Processing"
        img.save()

        TranslationTask.objects.all().delete()
        mock_delay.reset_mock()

        # Change core field
        img.set_current_language(self.default_lang)
        img.name = "New Name"
        img.save()

        # Should NOT trigger because NO target fields are empty
        assert not mock_delay.called
