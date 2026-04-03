# backend/translation/tasks.py
"""
Celery tasks for asynchronous translation processing.
"""

import logging
import uuid
from typing import Any

from celery import shared_task
from requests.exceptions import RequestException

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from .models import TranslationTask
from .services import TranslationService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)  # type: ignore[untyped-decorator]
def translate_instance_task(
    self,
    model_name: str,
    instance_pk: int,
    language_code: str,
    method_name: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Async wrapper for TranslationService methods.
    """
    logger.info("Task start: %s(pk=%s, lang=%s)", method_name, instance_pk, language_code)

    try:
        Model = apps.get_model(model_name)
        instance = Model.objects.get(pk=instance_pk)
        content_type = ContentType.objects.get_for_model(Model)

        # Establish a unique ID for this execution (CELERY task ID or fresh UUID for manual runs)
        task_id = self.request.id or str(uuid.uuid4())

        # Mark as RUNNING
        _update_task_record(
            content_type,
            instance_pk,
            language_code,
            method_name,
            TranslationTask.Status.RUNNING,
            task_id,
        )

        # Execute translation - create service instance
        service = TranslationService.create_default()
        method = getattr(service, method_name)
        result, failures = method(instance, language_code, **kwargs)

        if failures:
            # failures is now a dict: {field: reason}
            failure_details = ", ".join(f"{f} ({r})" for f, r in failures.items())
            error_msg = f"Translation partially failed: {failure_details}"
            logger.warning(error_msg)
            _handle_task_failure(model_name, instance_pk, language_code, error_msg, task_id=task_id)
            return _task_result(
                model_name, instance_pk, language_code, method_name, result=result, error=error_msg
            )

        # Mark as COMPLETED
        _update_task_record(
            content_type,
            instance_pk,
            language_code,
            method_name,
            TranslationTask.Status.COMPLETED,
            task_id=task_id,
        )

        logger.info("Task success: %s(pk=%s, lang=%s)", method_name, instance_pk, language_code)
        return _task_result(model_name, instance_pk, language_code, method_name, result=result)

    except ObjectDoesNotExist:
        logger.info("Instance not found: %s(pk=%s)", model_name, instance_pk)
        _handle_task_failure(model_name, instance_pk, language_code, "Instance not found")
        return _task_result(
            model_name, instance_pk, language_code, method_name, error="Instance not found"
        )

    except RequestException as exc:
        logger.warning("Transient error: %s. Retrying...", exc)
        raise self.retry(exc=exc)  # noqa: B904

    except Exception as exc:
        logger.exception("Task failed: %s(pk=%s, lang=%s)", method_name, instance_pk, language_code)
        _handle_task_failure(model_name, instance_pk, language_code, str(exc))
        return _task_result(model_name, instance_pk, language_code, method_name, error=str(exc))


def _update_task_record(
    content_type: ContentType,
    object_id: Any,
    language: str,
    method: str,
    status: str,
    task_id: str | None = None,
) -> None:
    """Updates or creates a TranslationTask record."""
    defaults: dict[str, Any] = {
        "method": method,
        "status": status,
        "content_type": content_type,
        "object_id": str(object_id),
        "language": language,
    }
    if status != TranslationTask.Status.FAILED:
        defaults["error_message"] = ""

    # If we have a specific task_id, that's our primary anchor.
    if task_id:
        TranslationTask.objects.update_or_create(task_id=task_id, defaults=defaults)
    else:
        # Fallback to broad match but avoid MultipleObjectsReturned
        task = (
            TranslationTask.objects.filter(
                content_type=content_type,
                object_id=str(object_id),
                language=language,
                method=method,
            )
            .order_by("-created_at")
            .first()
        )
        if task:
            for key, value in defaults.items():
                setattr(task, key, value)
            task.save()
        else:
            # Create new if nothing found
            TranslationTask.objects.create(
                **defaults,
                task_id=f"internal-{status}-{object_id}-{language}",  # dummy for manual runs
            )


def _handle_task_failure(
    model_name: str, instance_pk: Any, language: str, error: str, task_id: str | None = None
) -> None:
    """Safely updates task status to FAILED."""
    try:
        Model = apps.get_model(model_name)
        content_type = ContentType.objects.get_for_model(Model)

        # If we have a task_id, update that specific record first
        if task_id:
            TranslationTask.objects.filter(task_id=task_id).update(
                status=TranslationTask.Status.FAILED, error_message=error[:500]
            )
            return

        # Target the latest record for this instance/language as fallback
        task = (
            TranslationTask.objects.filter(
                content_type=content_type, object_id=str(instance_pk), language=language
            )
            .order_by("-created_at")
            .first()
        )
        if task:
            task.status = TranslationTask.Status.FAILED
            task.error_message = error[:500]
            task.save()
    except Exception:
        logger.exception("Failed to update task status to FAILED")


def _task_result(
    model: str, pk: Any, language: str, method: str, result: Any = None, error: str | None = None
) -> dict[str, Any]:
    """Standardizes task return format."""
    data = {"model": model, "pk": pk, "language": language, "method": method, "result": result}
    if error:
        data["error"] = error
    return data
