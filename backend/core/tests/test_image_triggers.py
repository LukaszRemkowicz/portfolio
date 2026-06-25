from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile

from astrophotography.forms import MainPageBackgroundImageForm
from astrophotography.tests.factories import MainPageBackgroundImageFactory
from common.tests.image_helpers import jpeg_field
from core.tasks import process_image_task


@pytest.mark.django_db
class TestBaseImageAsyncTrigger:
    def test_save_triggers_background_task_and_skips_sync_conversion(self):
        """
        Verify that saving a BaseImage (via MainPageBackgroundImage)
        triggers the Celery task and does NOT populate variants synchronously.
        """
        with patch("core.models.process_image_task.delay_on_commit") as mock_delay:
            # build() does not call save()
            img = MainPageBackgroundImageFactory.build()
            img.original = jpeg_field("new_upload.jpg")
            img.save()

            # Assert task was triggered with correct args
            # Using ANY for pk because it's generated on save
            mock_delay.assert_called_once()
            args, _ = mock_delay.call_args
            assert args[0] == "astrophotography"
            assert args[1] == "mainpagebackgroundimage"
            assert args[3] == ["original"]

            # Assert variants are STILL EMPTY (processing hasn't happened yet)
            img.refresh_from_db()
            assert img.variants.count() == 0
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
        Metadata-only saves must not clear generated variants when the source is unchanged.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)
        img.refresh_from_db()
        variant_names = {variant.file.name for variant in img.variants.all()}

        img.name = "Updated background title"
        img.save()
        img.refresh_from_db()

        assert {variant.file.name for variant in img.variants.all()} == variant_names

    def test_replacing_source_removes_old_derived_files(self):
        """
        Replacing the source image must delete previous generated variant files.
        """
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background-original.jpg", size=(2600, 1734))
            )

        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)
        img.refresh_from_db()
        old_variant_names = {variant.file.name for variant in img.variants.all()}
        assert old_variant_names
        assert all(img.original.storage.exists(name) for name in old_variant_names)

        image_io = BytesIO()
        Image.new("RGB", (64, 64), color="teal").save(image_io, "PNG")
        image_io.seek(0)
        replacement = SimpleUploadedFile(
            "background_refresh.png", image_io.read(), content_type="image/png"
        )

        with patch("core.models.process_image_task.delay_on_commit"):
            img.original = replacement
            img.save()
        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk, ["original"])
        img.refresh_from_db()

        assert all(not img.original.storage.exists(name) for name in old_variant_names)
        assert old_variant_names.isdisjoint({variant.file.name for variant in img.variants.all()})
