import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.db import transaction

from core.cache_service import CacheService

from .services import AstroImageExposureTimeService

if TYPE_CHECKING:
    from .models import AstroImage

logger: logging.Logger = logging.getLogger(__name__)


def calculate_astroimage_exposure_hours_task(astro_image_id: str) -> dict[str, int | str | float]:
    """Parse and persist one AstroImage exposure duration, then clear dependent caches."""
    try:
        astro_image_model = apps.get_model("astrophotography", "AstroImage")
        astro_image: AstroImage = astro_image_model.objects.get(pk=astro_image_id)
        service: AstroImageExposureTimeService = AstroImageExposureTimeService.create_default()
        exposure_details: str = service.get_exposure_details(astro_image)
        parsed_hours: float = service.parse_total_hours(exposure_details)

        # The row lock makes the check-and-write atomic against a concurrent admin save.
        with transaction.atomic():
            if not astro_image_model.objects.select_for_update().filter(pk=astro_image.pk).exists():
                return {"status": "skipped", "astro_image_id": astro_image_id}
            current_details = (
                astro_image_model.objects.filter(
                    pk=astro_image.pk, translations__language_code=settings.DEFAULT_APP_LANGUAGE
                )
                .values_list("translations__exposure_details", flat=True)
                .first()
            )
            updated = (
                astro_image_model.objects.filter(pk=astro_image.pk).update(
                    calculated_exposure_hours=parsed_hours
                )
                if (current_details or "") == exposure_details
                else 0
            )
        if not updated:
            logger.info("Discarded stale exposure calculation for AstroImage %s", astro_image_id)
            return {"status": "skipped", "astro_image_id": astro_image_id}
        CacheService.invalidate_landing_page_cache()

        logger.info(
            "Stored %s calculated exposure hour(s) for AstroImage %s",
            parsed_hours,
            astro_image_id,
        )
        result: dict[str, int | str | float] = {
            "status": "success",
            "astro_image_id": astro_image_id,
            "parsed_hours": parsed_hours,
        }
        return result
    except Exception:
        logger.exception("Failed to calculate exposure hours for AstroImage %s", astro_image_id)
        raise
