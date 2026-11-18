from unittest.mock import MagicMock, patch

import pytest

from astrophotography.services import AstroImageExposureTimeService
from astrophotography.tasks import calculate_astroimage_exposure_hours_task
from astrophotography.tests.factories import AstroImageFactory


@pytest.mark.django_db
@pytest.mark.parametrize(("replacement", "expected"), [("", 0), ("9 hours", 9)])
def test_stale_calculation_does_not_overwrite_new_exposure(replacement, expected):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        image = AstroImageFactory(exposure_details="2 hours", calculated_exposure_hours=2)
        service = AstroImageExposureTimeService(MagicMock())

        def parse(text):
            assert text == "2 hours"
            image.exposure_details = replacement
            image.save()
            if replacement:
                type(image).objects.filter(pk=image.pk).update(calculated_exposure_hours=expected)
            return 2.0

        service.parse_total_hours = parse
        with patch(
            "astrophotography.tasks.AstroImageExposureTimeService.create_default",
            return_value=service,
        ):
            result = calculate_astroimage_exposure_hours_task(str(image.pk))
        image.refresh_from_db()
        assert image.calculated_exposure_hours == expected
        assert result["status"] == "skipped"


@pytest.mark.django_db
def test_unchanged_exposure_calculation_succeeds(mocker):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        image = AstroImageFactory(exposure_details="2 hours", calculated_exposure_hours=0)
    service = AstroImageExposureTimeService(MagicMock())
    service.parse_total_hours = lambda text: 2.0
    mocker.patch(
        "astrophotography.tasks.AstroImageExposureTimeService.create_default", return_value=service
    )
    cache = mocker.patch("astrophotography.tasks.CacheService.invalidate_landing_page_cache")
    result = calculate_astroimage_exposure_hours_task(str(image.pk))
    image.refresh_from_db()
    assert image.calculated_exposure_hours == 2
    assert result["status"] == "success"
    cache.assert_called_once()
