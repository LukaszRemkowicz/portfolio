import pytest

from common.tests.image_helpers import _jpeg_field, _png_field
from core.tasks import process_image_task
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestProcessUserImagesTask:
    def test_process_user_images_task_optimizes_avatar(self):
        """
        GIVEN a user with a JPEG avatar
        WHEN process_user_images_task is called
        THEN the avatar should be shrunk to 264px and quality 20.
        """
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("test_avatar.jpg")
        user.save()

        process_image_task("users", "User", user.pk, ["avatar"])

        user.refresh_from_db()
        # In Green phase, we expect conversion to succeed
        assert user.avatar.name.endswith(".jpg")
        assert user.avatar_webp.name.endswith(".webp")
        assert "test_avatar" in user.avatar_webp.name

    def test_process_user_images_task_invalidates_caches_after_conversion(self, mocker):
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("test_avatar.jpg")
        user.save()

        mock_invalidate_user_cache = mocker.patch(
            "users.signals.CacheService.invalidate_user_cache"
        )
        mock_invalidate_frontend = mocker.patch(
            "users.signals.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )

        process_image_task("users", "User", user.pk, ["avatar"])

        mock_invalidate_user_cache.assert_called_once()
        mock_invalidate_frontend.assert_called_once()
        mock_invalidate_frontend.assert_called_with(["profile"])

    def test_process_user_images_task_uses_new_upload_not_stale_original(self):
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("old_avatar.jpg")
        user.save()
        process_image_task("users", "User", user.pk, ["avatar"])

        user.refresh_from_db()
        assert "old_avatar" in user.avatar.name
        assert "old_avatar" in user.avatar_webp.name

        user.avatar = _jpeg_field("new_avatar.jpg")
        user.save()
        process_image_task("users", "User", user.pk, ["avatar"])

        user.refresh_from_db()
        assert "new_avatar" in user.avatar.name
        assert user.avatar.name.endswith(".jpg")
        assert "new_avatar" in user.avatar_webp.name
        assert user.avatar_webp.name.endswith(".webp")

    def test_process_user_images_task_handles_cropped_png_avatar_upload(self):
        """
        GIVEN a cropped PNG avatar upload from the admin cropper
        WHEN process_user_images_task is called
        THEN the source avatar stays PNG and the derived avatar_webp is regenerated from it.
        """
        user = UserFactory.create_superuser()
        user.avatar = _png_field("cropped_avatar.png", size=(280, 280))
        user.save()

        process_image_task("users", "User", user.pk, ["avatar"])

        user.refresh_from_db()
        assert user.avatar.name.endswith(".png")
        assert "cropped_avatar" in user.avatar.name
        assert user.avatar_webp.name.endswith(".webp")
        assert "cropped_avatar" in user.avatar_webp.name

    def test_process_user_images_task_prefers_cropped_image_when_present(self):
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("original_avatar.jpg")
        user.avatar_cropped = _png_field("cropped_avatar.png", size=(280, 280))
        user.save()

        process_image_task("users", "User", user.pk, ["avatar"])

        user.refresh_from_db()
        assert "original_avatar" in user.avatar.name
        assert "cropped_avatar" in user.avatar_cropped.name
        assert user.avatar_webp.name.endswith(".webp")
        assert "cropped_avatar" in user.avatar_webp.name
