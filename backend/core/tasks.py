import logging

import sentry_sdk
from celery import shared_task

from django.apps import apps
from django.conf import settings
from django.db.models import Sum

from common.celery import CommitAwareTask
from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService
from core.services import LandingPageTotalTimeSpentService

logger = logging.getLogger(__name__)


def _get_astro_image_model():
    """Resolve AstroImage lazily without a module-level import cycle."""
    return apps.get_model("astrophotography", "AstroImage")


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
        print(f"DEBUG: Task updated fields: {updated_fields} for {instance_id}")
        instance.save(update_fields=updated_fields)
        logger.info(f"Successfully processed image for {app_label}.{model_name} {instance_id}")


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    name="core.recalculate_landing_page_total_time_spent",
    base=CommitAwareTask,
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
)
def recalculate_landing_page_total_time_spent_task(
    self,
    astro_image_id: str | None = None,
) -> dict[str, int | str | float]:
    """Return the current total time spent derived from stored AstroImage values."""
    try:
        AstroImage = _get_astro_image_model()
        aggregate = AstroImage.objects.aggregate(total=Sum("calculated_exposure_hours"))
        total_hours = float(aggregate["total"] or 0)

        CacheService.invalidate_landing_page_cache()
        invalidate_frontend_ssr_cache_task.delay(["settings"])

        logger.info(
            "Recalculated landing page total time spent to %s hour(s)%s",
            total_hours,
            f" after AstroImage {astro_image_id}" if astro_image_id else "",
        )
        return {
            "status": "success",
            "astro_image_id": astro_image_id or "",
            "total_time_spent": total_hours,
        }
    except Exception as exc:
        logger.exception("Failed to recalculate landing page total time spent")
        if settings.ENABLE_SENTRY:
            sentry_sdk.capture_exception(exc)
        raise self.retry(exc=exc) from exc


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    name="core.calculate_astroimage_exposure_hours",
    base=CommitAwareTask,
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
)
def calculate_astroimage_exposure_hours_task(
    self, astro_image_id: str
) -> dict[str, int | str | float]:
    """Parse and persist one AstroImage exposure duration, then refresh the global total."""
    try:
        AstroImage = _get_astro_image_model()
        astro_image = AstroImage.objects.get(pk=astro_image_id)
        exposure_details = (
            astro_image.safe_translation_getter(
                "exposure_details",
                language_code=settings.DEFAULT_APP_LANGUAGE,
                any_language=False,
            )
            or astro_image.safe_translation_getter("exposure_details", any_language=True)
            or ""
        )
        service = LandingPageTotalTimeSpentService.create_default()
        parsed_hours = service.parse_total_hours(str(exposure_details))

        AstroImage.objects.filter(pk=astro_image.pk).update(calculated_exposure_hours=parsed_hours)
        total_result = recalculate_landing_page_total_time_spent_task(
            astro_image_id=str(astro_image.pk)
        )

        logger.info(
            "Stored %s calculated exposure hour(s) for AstroImage %s",
            parsed_hours,
            astro_image_id,
        )
        return {
            "status": "success",
            "astro_image_id": astro_image_id,
            "parsed_hours": parsed_hours,
            "total_time_spent": total_result["total_time_spent"],
        }
    except Exception as exc:
        logger.exception("Failed to calculate exposure hours for AstroImage %s", astro_image_id)
        if settings.ENABLE_SENTRY:
            sentry_sdk.capture_exception(exc)
        raise self.retry(exc=exc) from exc
