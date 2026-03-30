import pytest

from common.tests.image_helpers import _jpeg_field
from users.tasks import process_user_images_task
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserAsyncTrigger:
    def test_save_triggers_user_images_task_on_commit(self, mocker):
        """
        Verify that saving a User triggers the specialized commit-aware task helper.
        """
        user = UserFactory.create_superuser()
        mock_delay = mocker.patch.object(process_user_images_task, "delay_on_commit")
        user.avatar = _jpeg_field("new.jpg")
        user.save()

        mock_delay.assert_called_once_with(user.pk, ["avatar"])
