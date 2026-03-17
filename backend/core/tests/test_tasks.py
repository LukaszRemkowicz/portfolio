from unittest.mock import patch

import pytest

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from core.tasks import process_image_task


@pytest.mark.django_db
class TestProcessImageTask:
    def test_process_image_task_converts_to_webp(self):
        """
        GIVEN an instance with a JPEG path
        WHEN process_image_task is called
        THEN the path should be converted to WebP and legacy_path populated.
        """
        # Prevent automatic task execution during factory creation for this test
        with patch("core.models.transaction.on_commit", side_effect=lambda f: None):
            img = MainPageBackgroundImageFactory()

        # Now manually call the task
        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)

        img.refresh_from_db()
        # In Green phase, we expect conversion to succeed
        assert img.path.name.endswith(".webp")
        # legacy_path should exist
        assert img.legacy_path
        assert img.legacy_path.name.endswith(".jpg")
