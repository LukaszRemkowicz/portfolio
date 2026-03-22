import logging
from typing import List

from celery import shared_task

from django.apps import apps

from common.celery import CommitAwareTask
from common.utils.image import convert_to_webp

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    name="users.process_user_images",
    base=CommitAwareTask,
)
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
    original_field_map = {
        "avatar": "avatar_original_image",
        "about_me_image": "about_me_image_original_image",
        "about_me_image2": "about_me_image2_original_image",
    }

    for field_name in changed_field_names:
        original_field_name = original_field_map.get(field_name)
        if (
            not original_field_name
            or not hasattr(user, field_name)
            or not hasattr(user, original_field_name)
        ):
            continue

        if field_name == "avatar":
            spec = user.get_avatar_spec()
        else:
            spec = user.get_portrait_spec()
        image_field = getattr(user, field_name)
        original_field = getattr(user, original_field_name)

        if not image_field:
            continue

        # Perform conversion
        result = convert_to_webp(
            original_field or image_field,
            quality=spec.quality,
            max_dimension=spec.dimension,
            dimension_percentage=spec.dimension_percentage,
        )

        if result:
            original_name, webp_content = result
            # Update original-image field with the uploaded source filename
            setattr(user, original_field_name, original_name)

            # Save the new WebP content to the main field
            # We use save=False to avoid recursive calls to user.save()
            image_field.save(webp_content.name, webp_content, save=False)

            updated_fields.extend([field_name, original_field_name])
            logger.info(f"Successfully converted {field_name} to WebP for User {user_id}")
        else:
            logger.warning(f"Conversion skipped or failed for {field_name} on User {user_id}")

    if updated_fields:
        # Use update_fields to avoid re-triggering save() logic
        user.save(update_fields=updated_fields)
