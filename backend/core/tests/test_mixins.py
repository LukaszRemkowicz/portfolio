from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from astrophotography.models import Place  # Example model
from core.mixins import TranslationStatusMixin
from core.models import TranslationTask


class TestTranslationStatusMixin(TestCase):
    def setUp(self):
        self.mixin = TranslationStatusMixin()
        self.mixin.model = Place  # Mock usage on Place model
        self.factory = RequestFactory()
        self.place = Place.objects.create(name="Warsaw", country="PL")
        self.content_type = ContentType.objects.get_for_model(Place)

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
