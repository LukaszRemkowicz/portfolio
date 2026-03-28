import logging
from typing import List

from celery import shared_task

from django.apps import apps

from common.celery import CommitAwareTask
from common.tasks import invalidate_frontend_ssr_cache_task
from common.utils.image import convert_to_webp
from core.cache_service import CacheService

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    name="users.process_user_images",
    base=CommitAwareTask,
)
def process_user_images_task(user_id: int, changed_field_names: List[str]) -> None:
    """
    Background task to convert User source images to derived WebP fields.
    Handles specialized shrinkage (264px for avatars).
    """
    User = apps.get_model("users", "User")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for image processing.")
        return

    updated_fields = []
    webp_field_map = {
        "avatar": "avatar_webp",
        "about_me_image": "about_me_image_webp",
        "about_me_image2": "about_me_image2_webp",
    }

    for field_name in changed_field_names:
        webp_field_name = webp_field_map.get(field_name)
        if (
            not webp_field_name
            or not hasattr(user, field_name)
            or not hasattr(user, webp_field_name)
        ):
            continue

        if field_name == "avatar":
            spec = user.get_avatar_spec()
        else:
            spec = user.get_portrait_spec()
        image_field = getattr(user, field_name)
        webp_field = getattr(user, webp_field_name)
        if not image_field:
            setattr(user, webp_field_name, None)
            updated_fields.append(webp_field_name)
            continue

        if str(image_field.name).lower().endswith(".webp"):
            setattr(user, webp_field_name, image_field.name)
            updated_fields.append(webp_field_name)
            continue

        # Perform conversion
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
            updated_fields.append(webp_field_name)
            logger.info(f"Successfully converted {field_name} to WebP for User {user_id}")
        else:
            logger.warning(f"Conversion skipped or failed for {field_name} on User {user_id}")

    if updated_fields:
        # Use update_fields to avoid re-triggering save() logic
        user.save(update_fields=updated_fields + ["updated_at"])
        # The admin request clears caches before async WebP processing finishes.
        # Invalidate again after the processed image paths are persisted so BE/FE
        # never keep serving a stale avatar or portrait URL.
        CacheService.invalidate_user_cache()
        invalidate_frontend_ssr_cache_task.delay_on_commit(["profile"])
