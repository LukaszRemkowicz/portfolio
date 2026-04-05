import logging

import sentry_sdk
from celery import shared_task

from django.apps import apps
from django.conf import settings

from common.celery import CommitAwareTask
from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService
from core.services import LandingPageTotalTimeSpentService

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    name="astrophotography.calculate_astroimage_exposure_hours",
    base=CommitAwareTask,
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
)
def calculate_astroimage_exposure_hours_task(
    self, astro_image_id: str
) -> dict[str, int | str | float]:
    """Parse and persist one AstroImage exposure duration, then clear dependent caches."""
    try:
        AstroImage = apps.get_model("astrophotography", "AstroImage")
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
        CacheService.invalidate_landing_page_cache()
        invalidate_frontend_ssr_cache_task.delay(["settings"])

        logger.info(
            "Stored %s calculated exposure hour(s) for AstroImage %s",
            parsed_hours,
            astro_image_id,
        )
        return {
            "status": "success",
            "astro_image_id": astro_image_id,
            "parsed_hours": parsed_hours,
        }
    except Exception as exc:
        logger.exception("Failed to calculate exposure hours for AstroImage %s", astro_image_id)
        if settings.ENABLE_SENTRY:
            sentry_sdk.capture_exception(exc)
        raise self.retry(exc=exc) from exc
