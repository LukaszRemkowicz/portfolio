import logging

import sentry_sdk
from celery import shared_task

from django.apps import apps
from django.conf import settings

from common.celery import CommitAwareTask
from common.utils.image import convert_to_webp

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    name="shop.process_shop_settings_images",
    base=CommitAwareTask,
)
def process_shop_settings_images_task(instance_id: int) -> None:
    """
    Background task to convert ShopSettings source image to derived WebP fields.
    """
    ShopSettings = apps.get_model("shop", "ShopSettings")
    try:
        instance = ShopSettings.objects.get(pk=instance_id)
    except ShopSettings.DoesNotExist:
        logger.error(f"ShopSettings with id {instance_id} not found for image processing.")
        return

    try:
        updated_fields: list[str] = []
        spec = instance.get_image_spec()

        # Prefer the admin crop when present, otherwise fall back to the source upload.
        image_field = instance.image_cropped if instance.image_cropped else instance.image
        webp_field = instance.image_webp

        logger.info(
            "Processing shop settings image for instance %s (using_cropped=%s)",
            instance_id,
            bool(instance.image_cropped),
        )

        if not image_field:
            instance.image_webp = None
            updated_fields.append("image_webp")
            logger.info(
                "Cleared shop settings WebP for instance %s because no source image exists",
                instance_id,
            )
        elif str(image_field.name).lower().endswith(".webp"):
            instance.image_webp.name = image_field.name
            updated_fields.append("image_webp")
            logger.info("Reused existing WebP source for shop settings instance %s", instance_id)
        else:
            result = convert_to_webp(
                image_field,
                quality=spec.quality,
                max_dimension=spec.dimension,
                dimension_percentage=spec.dimension_percentage,
            )

            if result:
                _, webp_content = result
                # Save the derived WebP content without touching the original field.
                webp_field.save(webp_content.name, webp_content, save=False)
                updated_fields.append("image_webp")
                logger.info(
                    "Successfully converted shop settings background to WebP for instance %s",
                    instance_id,
                )
            else:
                instance.image_webp = None
                updated_fields.append("image_webp")
                logger.warning(
                    "Conversion skipped or failed for shop settings background on instance %s",
                    instance_id,
                )

        if updated_fields:
            instance.save(update_fields=updated_fields + ["updated_at"])
            logger.info(
                "Processed shop settings image for instance %s with updated fields %s",
                instance_id,
                updated_fields,
            )

    except Exception as exc:
        logger.exception("Failed to process shop settings images for instance %s", instance_id)
        if settings.ENABLE_SENTRY:
            sentry_sdk.capture_exception(exc)
        raise
