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
)
def translate_instance_task(
    self,
    model_name: str,
    instance_pk: Any,
    language_code: str,
    method_name: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Async wrapper for TranslationService methods.
    """
    logger.info(
        "Starting translation task: %s.%s(pk=%s, lang=%s)",
        model_name,
        method_name,
        instance_pk,
        language_code,
    )

    try:
        # Load instance
        Model = apps.get_model(model_name)
        instance = Model.objects.get(pk=instance_pk)

        # Create/Update TranslationTask (PENDING -> RUNNING)
        content_type = ContentType.objects.get_for_model(Model)
        task_record, created = TranslationTask.objects.update_or_create(
            content_type=content_type,
            object_id=str(instance_pk),
            language=language_code,
            defaults={
                "method": method_name,
                "status": TranslationTask.Status.RUNNING,
                "task_id": self.request.id or str(instance_pk),
                "error_message": "",
            },
        )

        # Call service method
        method = getattr(TranslationService, method_name)
        result = method(instance, language_code, **kwargs)

        # Update Status -> COMPLETED
        task_record.status = TranslationTask.Status.COMPLETED
        task_record.save()

        logger.info(
            "Translation completed: %s.%s(pk=%s, lang=%s)",
            model_name,
            method_name,
            instance_pk,
            language_code,
        )

        return {
            "model": model_name,
            "pk": instance_pk,
            "language": language_code,
            "method": method_name,
            "result": result,
        }

    except ObjectDoesNotExist:
        logger.error(f"Instance not found: {model_name}(pk={instance_pk}). Skipping translation.")
        # Mark as FAILED if record exists
        try:
            Model = apps.get_model(model_name)
            content_type = ContentType.objects.get_for_model(Model)
            TranslationTask.objects.filter(
                content_type=content_type, object_id=str(instance_pk), language=language_code
            ).update(status=TranslationTask.Status.FAILED, error_message="Instance not found")
        except Exception:
            pass

        return {
            "model": model_name,
            "pk": instance_pk,
            "language": language_code,
            "method": method_name,
            "result": None,
            "error": "Instance not found",
        }

    except RequestException as exc:
        # Retry only on network/API transient errors
        logger.warning(f"Transient error in translation task: {exc}. Retrying...")
        raise self.retry(exc=exc)

    except Exception as exc:
        # Log and mark as FAILED for all other errors (permanent/dev errors)
        logger.exception(
            "Translation task failed: %s.%s(pk=%s, lang=%s)",
            model_name,
            method_name,
            instance_pk,
            language_code,
        )

        try:
            Model = apps.get_model(model_name)
            content_type = ContentType.objects.get_for_model(Model)
            TranslationTask.objects.filter(
                content_type=content_type, object_id=str(instance_pk), language=language_code
            ).update(status=TranslationTask.Status.FAILED, error_message=str(exc)[:500])
        except Exception:
            pass

        # Do not retry on unknown exceptions to avoid infinite loops of permanent errors
        return {
            "model": model_name,
            "pk": instance_pk,
            "language": language_code,
            "method": method_name,
            "result": None,
            "error": str(exc),
        }
