import logging
from typing import List

from celery import shared_task

from django.apps import apps

from common.utils.image import convert_to_webp

logger = logging.getLogger(__name__)


@shared_task(name="users.process_user_images")  # type: ignore[untyped-decorator]
def process_user_images_task(user_id: int, changed_field_names: List[str]) -> None:
    """
    Background task to convert User images to WebP and handle legacy backups.
    Handles specialized shrinkage (264px for avatars).
    """
    User = apps.get_model("users", "User")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for image processing.")
        return

    updated_fields = []

    for field_name in changed_field_names:
        legacy_field_name = f"{field_name}_legacy"
        if not hasattr(user, field_name) or not hasattr(user, legacy_field_name):
            continue

        if field_name == "avatar":
            spec = user.get_avatar_spec()
        else:
            spec = user.get_portrait_spec()
        image_field = getattr(user, field_name)

        if not image_field:
            continue

        # Perform conversion
        result = convert_to_webp(
            image_field,
            quality=spec.quality,
            max_dimension=spec.dimension,
        )

        if result:
            original_name, webp_content = result
            # Update legacy field with the old filename
            setattr(user, legacy_field_name, original_name)

            # Save the new WebP content to the main field
            # We use save=False to avoid recursive calls to user.save()
            image_field.save(webp_content.name, webp_content, save=False)

            updated_fields.extend([field_name, legacy_field_name])
            logger.info(f"Successfully converted {field_name} to WebP for User {user_id}")
        else:
            logger.warning(f"Conversion skipped or failed for {field_name} on User {user_id}")

    if updated_fields:
        # Use update_fields to avoid re-triggering save() logic
        user.save(update_fields=updated_fields)
