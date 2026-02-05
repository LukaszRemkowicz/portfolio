# backend/core/tests/test_models.py
"""
Tests for Core models, specifically TranslationTask.
"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from astrophotography.models import Place
from core.tests.factories import TranslationTaskFactory
from translation.models import TranslationTask


class TestTranslationTask(TestCase):
    """Tests for TranslationTask model."""

    def setUp(self):
        self.place = Place.objects.create(name="Warsaw", country="PL")
        self.content_type = ContentType.objects.get_for_model(Place)

    def test_translation_task_creation(self):
        """Test creating a TranslationTask linked to a model instance."""
        task = TranslationTaskFactory(
            method="translate_place",
            content_object=self.place,
        )

        assert task.pk is not None
        assert task.content_object == self.place
        assert task.status == "PENDING"
        assert str(task) == "translate_place (pl): Pending"

    def test_translation_task_status_choices(self):
        """Test status choices are correctly defined."""
        task = TranslationTaskFactory(
            status=TranslationTask.Status.RUNNING,
            content_object=self.place,
        )
        assert task.status == "RUNNING"
        assert task.get_status_display() == "Running"

    def test_translation_task_generic_foreign_key(self):
        """Test GenericForeignKey works for fetching related object."""
        task = TranslationTaskFactory(
            content_object=self.place,
            language="de",
        )

        # Refresh from db
        fetched_task = TranslationTask.objects.get(pk=task.pk)
        assert fetched_task.content_object.pk == self.place.pk
        assert fetched_task.content_object.name == "Warsaw"
