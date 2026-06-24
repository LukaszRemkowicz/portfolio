from unittest.mock import patch

import pytest
from PIL import Image

from common.tests.image_helpers import jpeg_field, png_field
from core.tasks import process_image_task
from users.models import User


def _variant_name(superuser, source_name: str) -> str:
    variant = superuser.variants.get(role=f"{source_name}__original_format")
    return str(variant.file.name)


@pytest.mark.django_db
class TestProcessUserImagesTask:
    def test_process_user_images_task_generates_avatar_variant(self, superuser: User):
        superuser.avatar = jpeg_field("test_avatar.jpg", size=(800, 800))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()

        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        variant = superuser.variants.get(role="avatar__original_format")
        assert superuser.avatar.name.endswith(".jpg")
        assert variant.width == 800
        assert variant.file.name.endswith(".webp")
        assert "test_avatar" in variant.file.name

    def test_process_user_images_task_invalidates_caches_after_conversion(
        self, mocker, superuser: User
    ):
        superuser.avatar = jpeg_field("test_avatar.jpg", size=(800, 800))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()

        mock_invalidate_user_cache = mocker.patch(
            "users.signals.CacheService.invalidate_user_cache"
        )
        mock_invalidate_frontend = mocker.patch(
            "users.signals.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )

        process_image_task("users", "User", superuser.pk, ["avatar"])

        mock_invalidate_user_cache.assert_called_once()
        mock_invalidate_frontend.assert_called_once_with(["profile"])

    def test_process_user_images_task_uses_new_upload_not_stale_original(self, superuser: User):
        superuser.avatar = jpeg_field("old_avatar.jpg", size=(800, 800))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()
        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        first_variant_name = _variant_name(superuser, "avatar")
        assert "old_avatar" in first_variant_name

        superuser.avatar = jpeg_field("new_avatar.jpg", size=(800, 800))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()
        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        second_variant_name = _variant_name(superuser, "avatar")
        assert "new_avatar" in second_variant_name
        assert second_variant_name.endswith(".webp")
        assert first_variant_name != second_variant_name

    def test_process_user_images_task_handles_cropped_png_avatar_upload(self, superuser: User):
        superuser.avatar = png_field("cropped_avatar.png", size=(280, 280))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()

        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        variant = superuser.variants.get(role="avatar__original_format")
        assert superuser.avatar.name.endswith(".png")
        assert "cropped_avatar" in superuser.avatar.name
        assert variant.file.name.endswith(".webp")
        assert "cropped_avatar" in variant.file.name

    def test_process_user_images_task_prefers_cropped_image_when_present(self, superuser: User):
        superuser.avatar = jpeg_field("original_avatar.jpg")
        superuser.avatar_cropped = png_field("cropped_avatar.png", size=(280, 280))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()

        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        variant = superuser.variants.get(role="avatar__original_format")
        assert "original_avatar" in superuser.avatar.name
        assert "cropped_avatar" in superuser.avatar_cropped.name
        assert variant.file.name.endswith(".webp")
        assert "cropped_avatar" in variant.file.name

    def test_process_user_images_task_preserves_transparent_avatar_crop(self, superuser: User):
        superuser.avatar = jpeg_field("original_avatar.jpg")
        superuser.avatar_cropped = png_field("transparent_avatar.png", mode="RGBA", size=(280, 280))
        with patch("users.models.process_image_task.delay_on_commit"):
            superuser.save()

        process_image_task("users", "User", superuser.pk, ["avatar"])

        superuser.refresh_from_db()
        variant = superuser.variants.get(role="avatar__original_format")
        with variant.file.open("rb") as generated_file:
            image = Image.open(generated_file)
            image.load()

        assert image.mode == "RGBA"
        assert image.getchannel("A").getextrema()[0] == 0
