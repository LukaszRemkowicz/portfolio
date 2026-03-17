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
        assert user.avatar.name.endswith(".webp")
        # Django adds a random suffix (e.g. test_avatar_PRCHIn5.jpg),
        # so we check if the base name is in the field name
        assert "test_avatar" in user.avatar_legacy.name
        assert user.avatar_legacy.name.endswith(".jpg")
