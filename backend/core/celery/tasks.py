# backend/core/celery/tasks.py
"""
Celery tasks for asynchronous translation processing.

Key Design: Tasks are THIN WRAPPERS around TranslationService methods.
- Service handles all translation logic (GPT method selection, idempotency, saving)
- Tasks add async execution + retry capabilities
- DRY: Single source of truth in TranslationService
"""
import logging
from typing import Any

from celery import shared_task
from requests.exceptions import RequestException

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from core.models import TranslationTask
from core.services import TranslationService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    autoretry_for=(RequestException,),
)
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

    This task delegates ALL translation logic to the service:
    - Service checks if translation exists (_has_translation)
    - Service chooses correct GPT handler (translate, translate_html, translate_place, etc.)
    - Service saves translations with atomic transactions

    This task just adds:
    - Asynchronous execution via Celery
    - Retry on network/GPT failures
    - Background processing (non-blocking admin saves)

    Args:
        model_name: Full model path (e.g., "astrophotography.AstroImage")
        instance_pk: Primary key of the instance
        language_code: Target language code (e.g., "pl", "es")
        method_name: TranslationService method name (e.g., "translate_place")
        **kwargs: Extra context passed to service method (e.g., force=True for tags)

    Raises:
        Retry: On network errors, rate limits, or temporary GPT failures
    """

    logger.info(
        "Starting translation task: %s.%s(pk=%s, lang=%s)",
        model_name,
        method_name,
        instance_pk,
        language_code,
    )

    try:
        # 0. Load instance
        Model = apps.get_model(model_name)
        instance = Model.objects.get(pk=instance_pk)

        # 1. Create/Update TranslationTask (PENDING -> RUNNING)
        content_type = ContentType.objects.get_for_model(Model)
        task_record, created = TranslationTask.objects.update_or_create(
            content_type=content_type,
            object_id=str(instance_pk),
            language=language_code,
            defaults={
                "method": method_name,
                "status": TranslationTask.Status.RUNNING,
                "task_id": self.request.id or str(instance_pk),  # Fallback for local testing
                "error_message": "",
            },
        )

        # 2. Call service method (it handles everything: idempotency, GPT, saving)
        method = getattr(TranslationService, method_name)
        result = method(instance, language_code, **kwargs)

        # 3. Update Status -> COMPLETED
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
        # 3a. Update Status -> FAILED (if record exists, unlikely safely ignored)
        # Don't retry if object was deleted
        return {
            "model": model_name,
            "pk": instance_pk,
            "language": language_code,
            "method": method_name,
            "result": None,
            "error": "Instance not found",
        }

    except Exception as exc:
        logger.exception(
            "Translation task failed: %s.%s(pk=%s, lang=%s)",
            model_name,
            method_name,
            instance_pk,
            language_code,
        )

        # 3b. Update Status -> FAILED
        try:
            Model = apps.get_model(model_name)
            content_type = ContentType.objects.get_for_model(Model)
            TranslationTask.objects.filter(
                content_type=content_type, object_id=str(instance_pk), language=language_code
            ).update(status=TranslationTask.Status.FAILED, error_message=str(exc)[:500])
        except Exception:
            pass  # Don't let logging failure mask actual error

        # Retry on any other exception (network errors, GPT failures, etc.)
        raise self.retry(exc=exc)
