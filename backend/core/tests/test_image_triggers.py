from unittest.mock import patch

import pytest

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
        with patch.object(process_image_task, "delay") as mock_delay:
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
