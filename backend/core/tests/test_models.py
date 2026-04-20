# backend/core/tests/test_models.py
"""
Tests for Core models, specifically TranslationTask.
"""

from unittest.mock import patch

import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from astrophotography.models import Place
from astrophotography.tests.factories import MainPageBackgroundImageFactory
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


@pytest.mark.django_db
class TestBaseImageModel:
    def test_dispatch_image_processing_enqueues_task_for_changed_source(self):
        """
        Dispatch should enqueue the shared processing task when a canonical source
        exists and the save represents a new or changed source image.
        """
        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            img = MainPageBackgroundImageFactory()

        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            img._dispatch_image_processing(
                is_new=False,
                source_changed=True,
                update_fields=None,
            )

        mock_delay.assert_called_once_with(
            img._meta.app_label,
            img._meta.model_name,
            str(img.pk),
        )

    def test_dispatch_image_processing_skips_when_update_fields_are_present(self):
        """
        Dispatch should skip when save() is running a targeted update_fields write.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            img._dispatch_image_processing(
                is_new=False,
                source_changed=True,
                update_fields=["name"],
            )

        mock_delay.assert_not_called()

    def test_verify_storage_consistency_restores_previous_source_when_current_is_missing(self):
        """
        Save-time consistency checks must recover the previous source name when the
        freshly assigned current name is missing but the previous stored file still exists.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        img.refresh_from_db()
        previous_name = str(img.original.name)
        assert img.original.storage.exists(previous_name)

        img.original.name = "images/missing-current.jpg"

        img._verify_storage_consistency(
            is_new=False,
            source_changed=True,
            existing_source_name=previous_name,
        )

        assert str(img.original.name) == previous_name

    def test_verify_storage_consistency_raises_and_deletes_new_row_when_files_are_missing(self):
        """
        Save-time consistency checks must fail hard for a newly created row when neither
        the current nor previous source file exists.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        img.refresh_from_db()
        previous_name = str(img.original.name)
        img.original.storage.delete(previous_name)
        img.original.name = "images/missing-current.jpg"

        with pytest.raises(ValidationError, match="was not saved to storage"):
            img._verify_storage_consistency(
                is_new=True,
                source_changed=True,
                existing_source_name=previous_name,
            )

        assert not type(img).objects.filter(pk=img.pk).exists()

    def test_cleanup_old_files_deletes_requested_files(self):
        """
        Cleanup should remove previously tracked managed files by name.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        stale_name = "backgrounds/original/stale-file.jpg"
        img.original.storage.save(stale_name, img.original.file)
        assert img.original.storage.exists(stale_name)

        img._cleanup_old_files({stale_name})

        assert not img.original.storage.exists(stale_name)

    def test_cleanup_old_files_keeps_files_when_none_are_requested(self):
        """
        Cleanup should leave current files alone when no deletions were requested.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        current_name = str(img.original.name)
        assert img.original.storage.exists(current_name)

        img._cleanup_old_files(set())

        assert img.original.storage.exists(current_name)
