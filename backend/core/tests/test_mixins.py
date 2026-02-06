import uuid

import pytest
from pytest_mock import MockerFixture

from django.test import RequestFactory, override_settings

from astrophotography.models import Place
from translation.mixins import (
    AutomatedTranslationMixin,
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
        self.place = Place.objects.create(name="Warsaw", country="PL")

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
        TranslationTask.objects.create(
            content_object=self.place,
            task_id="task1",
            language="es",
            status=TranslationTask.Status.PENDING,
        )
        status_html = self.mixin.translation_status(self.place)
        assert "⏳ In Progress" in status_html
        assert "color:orange" in status_html

    def test_translation_status_completed(self):
        """Status should be 'Complete' if all tasks are COMPLETED."""
        TranslationTask.objects.create(
            content_object=self.place,
            task_id="task1",
            language="es",
            status=TranslationTask.Status.COMPLETED,
        )
        TranslationTask.objects.create(
            content_object=self.place,
            task_id="task2",
            language="fr",
            status=TranslationTask.Status.COMPLETED,
        )
        status_html = self.mixin.translation_status(self.place)
        assert "✅ Complete" in status_html
        assert "color:green" in status_html

    def test_translation_status_failed(self):
        """Status should be 'Failed' if any task FAILED."""
        TranslationTask.objects.create(
            content_object=self.place,
            task_id="task1",
            language="es",
            status=TranslationTask.Status.COMPLETED,
        )
        TranslationTask.objects.create(
            content_object=self.place,
            task_id="task2",
            language="fr",
            status=TranslationTask.Status.FAILED,
        )
        status_html = self.mixin.translation_status(self.place)
        assert "❌ Failed" in status_html
        assert "color:red" in status_html


@pytest.mark.django_db
class TestAutomatedTranslationMixin:
    def test_save_model_triggers_tasks_and_creates_records(self, mocker: MockerFixture):
        """Ensure save_model triggers celery tasks and creates TranslationTask records."""

        class BaseAdmin:
            def save_model(self, request, obj, form, change):
                pass

            def message_user(self, request, message, level):
                pass

        class MockAdmin(AutomatedTranslationMixin, BaseAdmin):
            translation_service_method = "translate_place"
            translation_trigger_fields = ["name"]

            def get_translation_kwargs(self, obj, form, change, should_trigger):
                return {"force": True}

        place = Place.objects.create(name="Warsaw", country="PL")
        admin_instance = MockAdmin()

        # Mock dependencies
        mock_task = mocker.patch("translation.mixins.translate_instance_task")
        mocker.patch(
            "translation.services.TranslationService.get_available_languages",
            return_value=["en", "pl", "es"],
        )
        with override_settings(PARLER_DEFAULT_LANGUAGE_CODE="en"):
            # Setup mock task return value with unique IDs
            def side_effect(*args, **kwargs):
                m = mocker.MagicMock()
                m.id = str(uuid.uuid4())
                return m

            mock_task.delay.side_effect = side_effect

            # Call save_model
            admin_instance.save_model(None, place, None, False)

        # Verify task calls
        # 'en' is default (skipped), 'pl' and 'es' should be called
        assert mock_task.delay.call_count == 2

        # Verify TranslationTask records created
        tasks = TranslationTask.objects.filter(object_id=place.pk)
        assert tasks.count() == 2
        assert tasks.filter(language="pl", status=TranslationTask.Status.PENDING).exists()
        assert tasks.filter(language="es", status=TranslationTask.Status.PENDING).exists()
