import inspect
from unittest.mock import patch

import pytest

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from common.tests.image_helpers import jpeg_field
from core import tasks
from core.models import ImageVariant
from core.tasks import process_image_task, run_shared_image_processing


def test_shared_image_processing_does_not_delegate_to_common_wrapper() -> None:
    task_source = inspect.getsource(tasks.run_shared_image_processing)

    assert "process_image_operations" not in task_source


@pytest.mark.django_db
class TestProcessImageTask:
    def test_process_image_task_generates_original_format_variant(self):
        """
        GIVEN an instance with a JPEG path
        WHEN process_image_task is called
        THEN the primary generated hero variant should be populated.
        """
        # Prevent automatic task execution during factory creation for this test
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background.jpg", size=(2600, 1734))
            )

        # Now manually call the task
        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)

        img.refresh_from_db()
        assert img.original
        assert img.original.name.endswith(".jpg")
        hero = img.variants.get(role="hero", width=2560)
        assert isinstance(hero, ImageVariant)
        assert hero.file.name.endswith(".webp")

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
