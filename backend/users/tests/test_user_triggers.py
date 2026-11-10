import pytest

from common.tests.image_helpers import jpeg_field
from core.tasks import process_image_task
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserAsyncTrigger:
    def test_save_triggers_user_images_task_on_commit(self, mocker):
        """
        Verify that saving a User triggers the specialized commit-aware task helper.
        """
        user = UserFactory.create_superuser()
        mock_delay = mocker.patch("users.models.submit")
        user.avatar = jpeg_field("new.jpg")
        user.save()

        mock_delay.assert_called_once_with(process_image_task, "users", "user", user.pk, ["avatar"])
