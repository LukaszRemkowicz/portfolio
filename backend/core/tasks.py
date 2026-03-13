import logging

from celery import shared_task

from django.apps import apps

logger = logging.getLogger(__name__)


@shared_task(name="core.process_image")  # type: ignore[untyped-decorator]
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

    updated_fields = []

    # 1. Convert to WebP
    # We call the internal method which we'll refactor to be task-safe
    if hasattr(instance, "_convert_to_webp"):
        # We need to ensure we don't trigger another save() that triggers another task
        # The internal _convert_to_webp currently calls self.path.save(..., save=False)
        result = instance._convert_to_webp()
        if result:
            updated_fields.extend(["path", "legacy_path"])

    # 2. Generate Thumbnail
    if hasattr(instance, "path") and instance.path and hasattr(instance, "make_thumbnail"):
        instance.thumbnail = instance.make_thumbnail(instance.path)
        updated_fields.append("thumbnail")

    if updated_fields:
        # Use update_fields to avoid re-triggering save() logic or translations
        # and to be efficient.
        print(f"DEBUG: Task updated fields: {updated_fields} for {instance_id}")
        instance.save(update_fields=updated_fields)
        logger.info(f"Successfully processed image for {app_label}.{model_name} {instance_id}")
