from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from common.tests.image_helpers import _jpeg_field
from core.tasks import process_image_task


@pytest.mark.django_db
class TestBaseImageAsyncTrigger:
    def test_save_triggers_background_task_and_skips_sync_conversion(self):
        """
        Verify that saving a BaseImage (via MainPageBackgroundImage)
        triggers the Celery task and does NOT populate original_image synchronously.
        """
        with patch.object(process_image_task, "delay_on_commit") as mock_delay:
            # build() does not call save()
            img = MainPageBackgroundImageFactory.build()
            # Manually assign new path to ensure FieldTracker sees it as changed
            img.path = _jpeg_field("new_upload.jpg")
            img.save()

            # Assert task was triggered with correct args
            # Using ANY for pk because it's generated on save
            mock_delay.assert_called_once()
            args, _ = mock_delay.call_args
            assert args[0] == "astrophotography"
            assert args[1] == "mainpagebackgroundimage"

            # Assert original_image is STILL EMPTY (conversion hasn't happened yet)
            img.refresh_from_db()
            assert not img.original_image

    def test_clean_fails_for_existing_row_when_current_image_is_missing(self):
        """
        Existing broken rows must fail validation when the current image file is missing.
        """
        with patch.object(process_image_task, "delay_on_commit") as mock_delay:
            img = MainPageBackgroundImageFactory()

        img.refresh_from_db()
        img.path.storage.delete(img.path.name)

        with pytest.raises(ValidationError, match="does not exist in storage"):
            img.clean()

        assert type(img).objects.filter(pk=img.pk).exists()
        mock_delay.assert_called_once()

    def test_replacing_existing_background_image_keeps_new_file_and_removes_old_file(self):
        """
        The shared BaseImage save flow must preserve the newly uploaded replacement file
        for background images and delete only the previous file.
        """
        img = MainPageBackgroundImageFactory()
        img.refresh_from_db()

        old_path = str(img.path.name)
        assert img.path.storage.exists(old_path)

        image_io = BytesIO()
        Image.new("RGB", (64, 64), color="navy").save(image_io, "PNG")
        image_io.seek(0)
        replacement = SimpleUploadedFile(
            "background_replacement.png", image_io.read(), content_type="image/png"
        )

        img.path = replacement
        img.save()
        img.refresh_from_db()

        new_path = str(img.path.name)
        assert new_path != old_path
        assert img.path.storage.exists(new_path)
        assert not img.path.storage.exists(old_path)
