# backend/translation/tasks.py
"""
Celery tasks for asynchronous translation processing.
"""

import logging
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

        # Mark as RUNNING
        _update_task_record(
            content_type,
            instance_pk,
            language_code,
            method_name,
            TranslationTask.Status.RUNNING,
            self.request.id or str(instance_pk),
        )

        # Execute translation
        method = getattr(TranslationService, method_name)
        result = method(instance, language_code, **kwargs)

        # Mark as COMPLETED
        _update_task_record(
            content_type, instance_pk, language_code, method_name, TranslationTask.Status.COMPLETED
        )

        logger.info("Task success: %s(pk=%s, lang=%s)", method_name, instance_pk, language_code)
        return _task_result(model_name, instance_pk, language_code, method_name, result=result)

    except ObjectDoesNotExist:
        logger.error("Instance not found: %s(pk=%s)", model_name, instance_pk)
        _handle_task_failure(model_name, instance_pk, language_code, "Instance not found")
        return _task_result(
            model_name, instance_pk, language_code, method_name, error="Instance not found"
        )

    except RequestException as exc:
        logger.warning("Transient error: %s. Retrying...", exc)
        raise self.retry(exc=exc)

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
    defaults: dict[str, Any] = {"method": method, "status": status}
    if task_id:
        defaults["task_id"] = task_id
    if status != TranslationTask.Status.FAILED:
        defaults["error_message"] = ""

    TranslationTask.objects.update_or_create(
        content_type=content_type,
        object_id=str(object_id),
        language=language,
        defaults=defaults,
    )


def _handle_task_failure(model_name: str, instance_pk: Any, language: str, error: str) -> None:
    """Safely updates task status to FAILED."""
    try:
        Model = apps.get_model(model_name)
        content_type = ContentType.objects.get_for_model(Model)
        TranslationTask.objects.filter(
            content_type=content_type, object_id=str(instance_pk), language=language
        ).update(status=TranslationTask.Status.FAILED, error_message=error[:500])
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
