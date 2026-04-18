from unittest.mock import patch

import pytest

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from core.tasks import process_image_task, run_shared_image_processing


@pytest.mark.django_db
class TestProcessImageTask:
    def test_process_image_task_converts_to_webp(self):
        """
        GIVEN an instance with a JPEG path
        WHEN process_image_task is called
        THEN the path should be converted to WebP and original_image populated.
        """
        # Prevent automatic task execution during factory creation for this test
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory()

        # Now manually call the task
        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)

        img.refresh_from_db()
        # In Green phase, we expect conversion to succeed
        assert img.path.name.endswith(".webp")
        # original_image should exist
        assert img.original_image
        assert img.original_image.name.endswith(".jpg")

    def test_run_shared_image_processing_logs_and_returns_when_model_missing(self, mocker) -> None:
        error_mock = mocker.patch("core.tasks.logger.error")

        run_shared_image_processing("missing_app", "MissingModel", "123")

        error_mock.assert_called_once()

    def test_process_image_task_reports_exception_to_sentry_when_enabled(self, mocker) -> None:
        mocker.patch("core.tasks.settings.ENABLE_SENTRY", True)
        run_mock = mocker.patch(
            "core.tasks.run_shared_image_processing",
            side_effect=RuntimeError("boom"),
        )
        sentry_mock = mocker.patch("core.tasks.sentry_sdk.capture_exception")
        exception_mock = mocker.patch("core.tasks.logger.exception")

        with pytest.raises(RuntimeError, match="boom"):
            process_image_task("astrophotography", "MainPageBackgroundImage", "123")

        run_mock.assert_called_once_with(
            "astrophotography",
            "MainPageBackgroundImage",
            "123",
            None,
        )
        exception_mock.assert_called_once()
        sentry_mock.assert_called_once()

    def test_process_image_task_skips_sentry_when_disabled(self, mocker) -> None:
        mocker.patch("core.tasks.settings.ENABLE_SENTRY", False)
        mocker.patch("core.tasks.run_shared_image_processing", side_effect=RuntimeError("boom"))
        sentry_mock = mocker.patch("core.tasks.sentry_sdk.capture_exception")

        with pytest.raises(RuntimeError, match="boom"):
            process_image_task("astrophotography", "MainPageBackgroundImage", "123")

        sentry_mock.assert_not_called()
