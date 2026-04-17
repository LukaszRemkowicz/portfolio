import logging

import sentry_sdk
from celery import shared_task

from django.apps import apps
from django.conf import settings

from common.celery import CommitAwareTask
from common.image_processing import process_image_operations

logger = logging.getLogger(__name__)


def run_shared_image_processing(
    app_label: str,
    model_name: str,
    instance_id: str | int,
    changed_field_names: list[str] | None = None,
) -> None:
    """Load a model instance and run the shared image-processing workflow."""
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError:
        logger.error("Model %s.%s or instance %s not found.", app_label, model_name, instance_id)
        return
    try:
        instance = Model.objects.get(pk=instance_id)
    except Model.DoesNotExist:
        logger.error("Model %s.%s or instance %s not found.", app_label, model_name, instance_id)
        return

    updated_fields = process_image_operations(instance, changed_field_names)
    if updated_fields:
        logger.info(
            "Processed images for %s.%s %s with updated fields %s",
            app_label,
            model_name,
            instance_id,
            updated_fields,
        )


@shared_task(  # type: ignore[untyped-decorator]
    name="core.process_image",
    base=CommitAwareTask,
)
def process_image_task(
    app_label: str,
    model_name: str,
    instance_id: str | int,
    changed_field_names: list[str] | None = None,
) -> None:
    """Shared image-processing task."""
    try:
        run_shared_image_processing(app_label, model_name, instance_id, changed_field_names)
    except Exception as exc:
        logger.exception(
            "Failed to process image for %s.%s %s",
            app_label,
            model_name,
            instance_id,
        )
        if settings.ENABLE_SENTRY:
            sentry_sdk.capture_exception(exc)
        raise
