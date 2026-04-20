from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from astrophotography.forms import MainPageBackgroundImageForm
from astrophotography.tests.factories import MainPageBackgroundImageFactory
from common.tests.image_helpers import _jpeg_field


@pytest.mark.django_db
class TestBaseImageAsyncTrigger:
    def test_save_triggers_background_task_and_skips_sync_conversion(self):
        """
        Verify that saving a BaseImage (via MainPageBackgroundImage)
        triggers the Celery task and does NOT populate original_webp synchronously.
        """
        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            # build() does not call save()
            img = MainPageBackgroundImageFactory.build()
            img.original = _jpeg_field("new_upload.jpg")
            img.save()

            # Assert task was triggered with correct args
            # Using ANY for pk because it's generated on save
            mock_delay.assert_called_once()
            args, _ = mock_delay.call_args
            assert args[0] == "astrophotography"
            assert args[1] == "mainpagebackgroundimage"

            # Assert original_webp is STILL EMPTY (conversion hasn't happened yet)
            img.refresh_from_db()
            assert not img.original_webp
            assert img.original

    def test_form_is_invalid_for_existing_row_when_current_image_is_missing(self):
        """
        Existing broken rows must be rejected by the admin form when the source file is missing.
        """
        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            img = MainPageBackgroundImageFactory()

        img.refresh_from_db()
        img.original.storage.delete(img.original.name)
        form = MainPageBackgroundImageForm(data={"name": img.name}, instance=img)

        assert not form.is_valid()
        assert "original_upload" in form.errors
        assert type(img).objects.filter(pk=img.pk).exists()
        mock_delay.assert_called_once()

    def test_replacing_existing_background_image_keeps_new_file_and_removes_old_file(self):
        """
        The shared BaseImage save flow must preserve the newly uploaded replacement file
        for background images and delete only the previous file.
        """
        img = MainPageBackgroundImageFactory()
        img.refresh_from_db()

        old_path = str(img.original.name)
        assert img.original.storage.exists(old_path)

        image_io = BytesIO()
        Image.new("RGB", (64, 64), color="navy").save(image_io, "PNG")
        image_io.seek(0)
        replacement = SimpleUploadedFile(
            "background_replacement.png", image_io.read(), content_type="image/png"
        )

        with patch("core.models.process_image_task.delay_on_commit"):
            img.original = replacement
            img.save()
        img.refresh_from_db()

        new_path = str(img.original.name)
        assert new_path != old_path
        assert img.original.storage.exists(new_path)
        assert not img.original.storage.exists(old_path)
        assert img.original
        assert str(img.original.name) == new_path

    def test_metadata_only_save_preserves_existing_derived_assets(self):
        """
        Metadata-only saves must not clear canonical derived files when the source is unchanged.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        img.original_webp.save("existing-derived.webp", ContentFile(b"webp"), save=True)
        img.thumbnail.save("existing-thumb.webp", ContentFile(b"thumb"), save=True)
        original_webp_name = str(img.original_webp.name)
        thumbnail_name = str(img.thumbnail.name)

        img.name = "Updated background title"
        img.save()
        img.refresh_from_db()

        assert str(img.original_webp.name) == original_webp_name
        assert str(img.thumbnail.name) == thumbnail_name

    def test_replacing_source_removes_old_derived_files(self):
        """
        Replacing the source image must delete the previous derived WebP and thumbnail files.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        img.original_webp.save("old-derived.webp", ContentFile(b"webp"), save=True)
        img.thumbnail.save("old-thumb.webp", ContentFile(b"thumb"), save=True)
        old_webp_name = str(img.original_webp.name)
        old_thumbnail_name = str(img.thumbnail.name)
        assert img.original_webp.storage.exists(old_webp_name)
        assert img.thumbnail.storage.exists(old_thumbnail_name)

        image_io = BytesIO()
        Image.new("RGB", (64, 64), color="teal").save(image_io, "PNG")
        image_io.seek(0)
        replacement = SimpleUploadedFile(
            "background_refresh.png", image_io.read(), content_type="image/png"
        )

        with patch("core.models.process_image_task.delay_on_commit"):
            img.original = replacement
            img.save()
        img.refresh_from_db()

        assert not img.original.storage.exists(old_webp_name)
        assert not img.original.storage.exists(old_thumbnail_name)
        if img.original_webp:
            assert str(img.original_webp.name) != old_webp_name
        if img.thumbnail:
            assert str(img.thumbnail.name) != old_thumbnail_name
