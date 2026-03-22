from unittest.mock import patch

import pytest

from common.tests.image_helpers import _jpeg_field
from users.tasks import process_user_images_task
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserAsyncTrigger:
    def test_save_triggers_user_images_task_and_skips_sync_conversion(self):
        """
        Verify that saving a User triggers the specialized Celery task
        and does NOT populate avatar_original_image synchronously.
        """
        user = UserFactory.create_superuser()
        # Initialize with an old image
        user.avatar = _jpeg_field("old.jpg")
        user.save()

        with patch.object(process_user_images_task, "delay") as mock_delay:
            # Change avatar to trigger has_changed
            user.avatar = _jpeg_field("new.jpg")
            user.save()

            # Assert task was triggered
            mock_delay.assert_called_once()
            args, _ = mock_delay.call_args
            assert args[0] == user.pk
            assert "avatar" in args[1]

            # Assert avatar_original_image is STILL EMPTY (conversion hasn't happened yet)
            user.refresh_from_db()
            assert not user.avatar_original_image
