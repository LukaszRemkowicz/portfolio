import logging
from typing import TYPE_CHECKING

from django.apps import apps

from common.background import submit
from common.tasks import invalidate_frontend_ssr_cache_task
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

        astro_image_model.objects.filter(pk=astro_image.pk).update(
            calculated_exposure_hours=parsed_hours
        )
        CacheService.invalidate_landing_page_cache()
        submit(invalidate_frontend_ssr_cache_task, ["settings"])

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
