import uuid

import pytest
from pytest_mock import MockerFixture

from django.test import RequestFactory, override_settings

from astrophotography.models import Place
from astrophotography.tests.factories import PlaceFactory
from core.tests.factories import TranslationTaskFactory
from translation.mixins import (
    AutomatedTranslationAdminMixin,
    TranslationStatusMixin,
)
from translation.models import TranslationTask


@pytest.mark.django_db
class TestTranslationStatusMixin:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mixin = TranslationStatusMixin()
        self.mixin.model = Place  # Mock usage on Place model
        self.factory = RequestFactory()
        self.place = PlaceFactory()
        # Clear auto-triggered tasks to allow testing status in isolation
        TranslationTask.objects.all().delete()

    def test_get_list_display_adds_column(self):
        """Ensure 'translation_status' is added to list_display."""

        class BaseAdmin:
            def get_list_display(self, request):
                return ("id", "name")

        class MockAdmin(TranslationStatusMixin, BaseAdmin):
            pass

        admin = MockAdmin()
        request = self.factory.get("/")
        list_display = admin.get_list_display(request)

        assert "translation_status" in list_display
        assert list_display == ["id", "name", "translation_status"]

    def test_translation_status_not_started(self):
        """Status should be 'Not Started' when no tasks exist."""
        status_html = self.mixin.translation_status(self.place)
        assert "➖ Not Started" in status_html
        assert "color:gray" in status_html

    def test_translation_status_in_progress(self):
        """Status should be 'In Progress' if any task is PENDING or RUNNING."""
        TranslationTaskFactory(content_object=self.place)
        status_html = self.mixin.translation_status(self.place)
        assert "⏳ In Progress" in status_html
        assert "color:orange" in status_html

    def test_translation_status_completed(self):
        """Status should be 'Complete' if all tasks are COMPLETED."""
        TranslationTaskFactory(
            content_object=self.place,
            status=TranslationTask.Status.COMPLETED,
        )
        TranslationTaskFactory(
            content_object=self.place,
            language="fr",
            status=TranslationTask.Status.COMPLETED,
        )
        status_html = self.mixin.translation_status(self.place)
        assert "✅ Complete" in status_html
        assert "color:green" in status_html

    def test_translation_status_failed(self):
        """Status should be 'Failed' if any task FAILED."""
        TranslationTaskFactory(
            content_object=self.place,
            status=TranslationTask.Status.COMPLETED,
        )
        TranslationTaskFactory(
            content_object=self.place,
            language="fr",
            status=TranslationTask.Status.FAILED,
        )
        status_html = self.mixin.translation_status(self.place)
        assert "❌ Failed" in status_html
        assert "color:red" in status_html


@pytest.mark.django_db
class TestAutomatedTranslationAdminMixin:
    def test_save_model_triggers_tasks_and_creates_records(
        self, mocker: MockerFixture, mock_translate_task, mock_get_available_languages
    ):
        """Ensure save_model triggers celery tasks and creates TranslationTask records."""

        class BaseAdmin:
            def save_model(self, request, obj, form, change):
                pass

            def message_user(self, request, message, level):
                pass

        class MockAdmin(AutomatedTranslationAdminMixin, BaseAdmin):
            def get_translation_kwargs(self, obj, form, change, should_trigger):
                return {"force": True}

        mock_get_available_languages.return_value = ["en", "pl", "es"]

        # Setup mock task return value with unique IDs BEFORE factory creation
        def side_effect(*args, **kwargs):
            m = mocker.MagicMock()
            m.id = str(uuid.uuid4())
            return m

        mock_translate_task.delay.side_effect = side_effect

        place = PlaceFactory()
        # Reset mocks after factory creation to test save_model in isolation
        mock_translate_task.delay.reset_mock()
        TranslationTask.objects.all().delete()

        admin_instance = MockAdmin()

        with override_settings(DEFAULT_APP_LANGUAGE="en"):
            # Call save_model
            admin_instance.save_model(None, place, None, False)

        # Verify task calls
        # 'en' is default (skipped), 'pl' and 'es' should be called
        assert mock_translate_task.delay.call_count == 2

        # Verify TranslationTask records created
        tasks = TranslationTask.objects.filter(object_id=place.pk)
        assert tasks.count() == 2
        assert tasks.filter(language="pl", status=TranslationTask.Status.PENDING).exists()
        assert tasks.filter(language="es", status=TranslationTask.Status.PENDING).exists()
