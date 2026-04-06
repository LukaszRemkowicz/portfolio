import logging

import sentry_sdk
from celery import shared_task

from django.apps import apps
from django.conf import settings

from common.celery import CommitAwareTask

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    name="core.process_image",
    base=CommitAwareTask,
)
def process_image_task(app_label: str, model_name: str, instance_id: str) -> None:
    """
    Universal background task to process images (WebP conversion + thumbnails).
    Works for any model inheriting from BaseImage.
    """
    try:
        Model = apps.get_model(app_label, model_name)
        instance = Model.objects.get(pk=instance_id)
    except (LookupError, Model.DoesNotExist):
        logger.error(f"Model {app_label}.{model_name} or instance {instance_id} not found.")
        return

    try:
        updated_fields = []

        # 1. Convert to WebP
        # We call the internal method which we'll refactor to be task-safe
        if hasattr(instance, "_convert_to_webp"):
            # We need to ensure we don't trigger another save() that triggers another task
            # The internal _convert_to_webp currently calls self.path.save(..., save=False)
            result = instance._convert_to_webp()
            if result:
                updated_fields.extend(["path", "original_image"])

        # 2. Generate Thumbnail
        if hasattr(instance, "path") and instance.path and hasattr(instance, "make_thumbnail"):
            thumbnail_source = (
                instance.get_thumbnail_source()
                if hasattr(instance, "get_thumbnail_source")
                else instance.path
            )
            instance.thumbnail = instance.make_thumbnail(thumbnail_source)
            updated_fields.append("thumbnail")

        if updated_fields:
            # Use update_fields to avoid re-triggering save() logic or translations
            # and to be efficient.
            instance.save(update_fields=updated_fields)
            logger.info(
                "Processed image for %s.%s %s with updated fields %s",
                app_label,
                model_name,
                instance_id,
                updated_fields,
            )
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
