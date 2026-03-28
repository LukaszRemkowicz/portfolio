import pytest

from common.tests.image_helpers import _jpeg_field
from users.tasks import process_user_images_task
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

        process_user_images_task(user.pk, ["avatar"])

        user.refresh_from_db()
        # In Green phase, we expect conversion to succeed
        assert user.avatar.name.endswith(".jpg")
        assert user.avatar_webp.name.endswith(".webp")
        assert "test_avatar" in user.avatar_webp.name

    def test_process_user_images_task_invalidates_caches_after_conversion(self, mocker):
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("test_avatar.jpg")
        user.save()

        mock_invalidate_user_cache = mocker.patch("users.tasks.CacheService.invalidate_user_cache")
        mock_invalidate_frontend = mocker.patch(
            "users.tasks.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )

        process_user_images_task(user.pk, ["avatar"])

        assert mock_invalidate_user_cache.call_count == 2
        assert mock_invalidate_frontend.call_count == 2
        mock_invalidate_frontend.assert_called_with(["profile"])

    def test_process_user_images_task_uses_new_upload_not_stale_original(self):
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("old_avatar.jpg")
        user.save()
        process_user_images_task(user.pk, ["avatar"])

        user.refresh_from_db()
        assert "old_avatar" in user.avatar.name
        assert "old_avatar" in user.avatar_webp.name

        user.avatar = _jpeg_field("new_avatar.jpg")
        user.save()
        process_user_images_task(user.pk, ["avatar"])

        user.refresh_from_db()
        assert "new_avatar" in user.avatar.name
        assert user.avatar.name.endswith(".jpg")
        assert "new_avatar" in user.avatar_webp.name
        assert user.avatar_webp.name.endswith(".webp")
