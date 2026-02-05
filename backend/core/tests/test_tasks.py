# backend/core/tests/test_tasks.py
"""
Tests for Celery translation tasks.
"""
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import RequestException

from django.core.exceptions import ObjectDoesNotExist

from core.celery.tasks import translate_instance_task


@pytest.mark.django_db
class TestTranslateInstanceTask:
    """Tests for translate_instance_task."""

    def test_translate_instance_task_calls_service_method(self):
        """Task should call TranslationService method and create TranslationTask."""
        with (
            patch("core.celery.tasks.apps.get_model") as mock_get_model,
            patch("core.celery.tasks.TranslationService") as mock_service,
            patch("core.celery.tasks.TranslationTask") as mock_task_model,
            patch("core.celery.tasks.ContentType"),
        ):
            # Setup mocks
            mock_model = Mock()
            mock_instance = Mock()
            mock_instance.pk = 1
            mock_model.objects.get.return_value = mock_instance
            mock_get_model.return_value = mock_model

            mock_service.translate_place = Mock(return_value={"name": "Warszawa"})

            # Mock TranslationTask.objects.update_or_create
            mock_task_record = Mock()
            mock_task_model.objects.update_or_create.return_value = (
                mock_task_record,
                True,
            )

            # Call task
            translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=1,
                language_code="pl",
                method_name="translate_place",
            )

            # Verify TranslationTask created (RUNNING)
            mock_task_model.objects.update_or_create.assert_called_once()
            _, kwargs = mock_task_model.objects.update_or_create.call_args
            assert kwargs["defaults"]["status"] == mock_task_model.Status.RUNNING
            assert kwargs["language"] == "pl"

            # Verify service method called
            mock_service.translate_place.assert_called_once_with(mock_instance, "pl")

            # Verify status updated to COMPLETED
            assert mock_task_record.status == mock_task_model.Status.COMPLETED
            mock_task_record.save.assert_called_once()

    def test_translate_instance_task_handles_missing_instance(self):
        """Task should gracefully handle deleted instances without retrying."""
        with (
            patch("core.celery.tasks.apps.get_model") as mock_get_model,
            patch("core.celery.tasks.TranslationTask") as mock_task_model,
            patch("core.celery.tasks.ContentType"),
        ):
            # Setup mock to raise ObjectDoesNotExist
            mock_model = Mock()
            mock_model.objects.get.side_effect = ObjectDoesNotExist("Not found")
            mock_get_model.return_value = mock_model

            # Mock TranslationTask (should fail update gracefully)
            mock_task_model.objects.update_or_create.return_value = (Mock(), True)

            # Call task
            _result = translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=999,
                language_code="pl",
                method_name="translate_place",
            )

            # Verify error handling
            assert _result["model"] == "astrophotography.Place"
            assert _result["pk"] == 999
            assert _result["result"] is None
            assert _result["error"] == "Instance not found"

    def test_translate_instance_task_inherits_idempotency(self):
        """Task should not re-translate if translation exists (service handles this)."""
        with (
            patch("core.celery.tasks.apps.get_model") as mock_get_model,
            patch("core.celery.tasks.TranslationService") as mock_service,
            patch("core.celery.tasks.TranslationTask") as mock_task_model,
            patch("core.celery.tasks.ContentType"),
        ):
            # Setup mocks
            mock_model = Mock()
            mock_instance = Mock()
            mock_instance.pk = 1
            mock_model.objects.get.return_value = mock_instance
            mock_get_model.return_value = mock_model

            # Mock TranslationTask
            mock_task_model.objects.update_or_create.return_value = (Mock(), True)

            # Service returns existing translation (skipped GPT call)
            mock_service.translate_place = Mock(return_value={"name": "Existing translation"})

            # Call task twice
            result1 = translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=1,
                language_code="pl",
                method_name="translate_place",
            )

            result2 = translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=1,
                language_code="pl",
                method_name="translate_place",
            )

            # Service method called both times (but service internally skips GPT)
            assert mock_service.translate_place.call_count == 2

            # Both results successful
            assert result1["result"] == {"name": "Existing translation"}
            assert result2["result"] == {"name": "Existing translation"}

    def test_translate_instance_task_retry_on_request_exception(self):
        """Task should update status to FAILED on exception before retrying."""
        with (
            patch("core.celery.tasks.apps.get_model") as mock_get_model,
            patch("core.celery.tasks.TranslationService") as mock_service,
            patch("core.celery.tasks.TranslationTask") as mock_task_model,
            patch("core.celery.tasks.ContentType"),
        ):
            # Setup mocks
            mock_model = Mock()
            mock_instance = Mock()
            mock_instance.pk = 1
            mock_model.objects.get.return_value = mock_instance
            mock_get_model.return_value = mock_model

            # Mock update_or_create for initial RUNNING state
            mock_task_record = Mock()
            mock_task_model.objects.update_or_create.return_value = (
                mock_task_record,
                True,
            )

            # Simulate RequestException
            mock_service.translate_place = Mock(side_effect=RequestException("Connection error"))

            # Task should raise Retry/Exception
            with pytest.raises(Exception):
                translate_instance_task(
                    model_name="astrophotography.Place",
                    instance_pk=1,
                    language_code="pl",
                    method_name="translate_place",
                )

            # Verify status updated to FAILED via filter().update()
            mock_task_model.objects.filter.assert_called()
            mock_task_model.objects.filter.return_value.update.assert_called_with(
                status=mock_task_model.Status.FAILED, error_message="Connection error"
            )

    def test_translate_instance_task_passes_kwargs(self):
        """Task should pass kwargs (e.g., force=True) to service method."""
        with (
            patch("core.celery.tasks.apps.get_model") as mock_get_model,
            patch("core.celery.tasks.TranslationService") as mock_service,
            patch("core.celery.tasks.TranslationTask") as mock_task_model,
            patch("core.celery.tasks.ContentType"),
        ):
            # Setup mocks
            mock_model = Mock()
            mock_instance = Mock()
            mock_instance.pk = 5
            mock_model.objects.get.return_value = mock_instance
            mock_get_model.return_value = mock_model

            # Mock TranslationTask
            mock_task_model.objects.update_or_create.return_value = (Mock(), True)

            mock_service.translate_parler_tag = Mock(return_value=["Django", "Python"])

            # Call task with kwargs
            result = translate_instance_task(
                model_name="astrophotography.Tag",
                instance_pk=5,
                language_code="pl",
                method_name="translate_parler_tag",
                force=True,  # Passed as kwarg
            )

            # Verify kwargs passed to service
            mock_service.translate_parler_tag.assert_called_once_with(
                mock_instance, "pl", force=True
            )

            # Verify result
            assert result["result"] == ["Django", "Python"]
