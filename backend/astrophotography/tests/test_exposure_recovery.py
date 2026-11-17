from io import StringIO
from unittest.mock import patch
from uuid import UUID

import pytest

from django.core.management import call_command

from astrophotography.models import AstroImage
from astrophotography.tests.factories import AstroImageFactory


@pytest.mark.django_db
def test_clearing_default_exposure_resets_hours_without_task(mocker):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        image = AstroImageFactory(exposure_details="2 hours", calculated_exposure_hours=2)
    submit = mocker.patch("astrophotography.models.submit")
    invalidate = mocker.patch("astrophotography.signals.CacheService.invalidate_landing_page_cache")
    image.exposure_details = ""
    image.save()
    image.refresh_from_db()
    assert image.calculated_exposure_hours == 0
    submit.assert_not_called()
    invalidate.assert_called()


@pytest.mark.django_db
def test_recalculate_continues_after_failure_without_erasing_old_value(mocker):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        first = AstroImageFactory(id=UUID(int=1), calculated_exposure_hours=3)
        second = AstroImageFactory(id=UUID(int=2), calculated_exposure_hours=4)

    def calculate(pk):
        if pk == str(first.pk):
            raise ValueError("bad image")
        AstroImage.objects.filter(pk=pk).update(calculated_exposure_hours=6)

    mocker.patch(
        "astrophotography.management.commands.recalculate_landing_page_total_time_spent."
        "calculate_astroimage_exposure_hours_task",
        side_effect=calculate,
    )
    out = StringIO()
    call_command("recalculate_landing_page_total_time_spent", recalculate=True, stdout=out)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.calculated_exposure_hours == 3
    assert second.calculated_exposure_hours == 6
    assert str(first.pk) in out.getvalue()


@pytest.mark.django_db
def test_other_translation_does_not_clear_default_hours(mocker):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        image = AstroImageFactory(exposure_details="2 hours", calculated_exposure_hours=2)
    image.set_current_language("pl")
    image.name = "Test"
    image.exposure_details = ""
    submit = mocker.patch("astrophotography.models.submit")
    image.save()
    image.refresh_from_db()
    assert image.calculated_exposure_hours == 2
    submit.assert_not_called()


@pytest.mark.django_db
def test_partial_save_that_persists_translation_resets_hours(mocker):
    with patch("core.models.submit"), patch("astrophotography.models.submit"):
        image = AstroImageFactory(exposure_details="2 hours", calculated_exposure_hours=2)
    image.exposure_details = ""
    submit = mocker.patch("astrophotography.models.submit")
    image.save(update_fields=["slug"])
    image.refresh_from_db()
    assert image._get_saved_default_exposure_details() == ""
    assert image.calculated_exposure_hours == 0
    submit.assert_not_called()
