from io import StringIO

import pytest
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from django.core.management import call_command

from astrophotography.models import AstroImage, MainPageLocation, Place
from astrophotography.tests.factories import AstroImageFactory, PlaceFactory


@pytest.mark.django_db
class TestSeedRegionsCommand:
    def test_seed_regions_creates_regions_and_links_sub_places(self, mocker: MockerFixture) -> None:
        mocker.patch("astrophotography.models.Place.trigger_translations", autospec=True)

        call_command("seed_regions")

        canary_islands = Place.objects.translated("en", name="Canary Islands").get(is_region=True)
        tenerife = Place.objects.translated("en", name="Tenerife").get()

        assert canary_islands.sub_places.filter(pk=tenerife.pk).exists()
        assert canary_islands.country == "ES"

    def test_seed_regions_dry_run_writes_nothing(self, mocker: MockerFixture) -> None:
        mocker.patch("astrophotography.models.Place.trigger_translations", autospec=True)
        output = StringIO()

        call_command("seed_regions", dry_run=True, stdout=output)

        assert Place.objects.count() == 0
        assert "DRY RUN" in output.getvalue()


@pytest.mark.django_db
class TestFixParlerLanguageCodesCommand:
    def test_fix_parler_language_codes_updates_legacy_rows(self, mocker: MockerFixture) -> None:
        mocker.patch("astrophotography.models.Place.trigger_translations", autospec=True)
        mocker.patch("astrophotography.models.AstroImage.trigger_translations", autospec=True)
        mocker.patch("astrophotography.models.MainPageLocation.trigger_translations", autospec=True)
        mocker.patch("core.models.process_image_task.delay")

        place = PlaceFactory()
        translation_model = Place._parler_meta.root_model
        translation_model.objects.filter(master=place, language_code="en").delete()
        translation_model.objects.create(master=place, language_code="en-us", name="Tatras")

        astro_image = AstroImageFactory(place=place, thumbnail=None)
        astro_translation_model = AstroImage._parler_meta.root_model
        astro_translation_model.objects.filter(master=astro_image, language_code="en").delete()
        astro_translation_model.objects.create(
            master=astro_image,
            language_code="en-us",
            name="Legacy Astro",
            description="desc",
            exposure_details="exp",
            processing_details="proc",
        )

        location = MainPageLocation.objects.create(
            place=place,
            highlight_name="Tatras Adventure",
            is_active=True,
            adventure_date=DateRange("2025-01-01", "2025-01-31"),
        )
        location_translation_model = MainPageLocation._parler_meta.root_model
        location_translation_model.objects.filter(master=location, language_code="en").delete()
        location_translation_model.objects.create(
            master=location,
            language_code="en-us",
            story="Story",
            highlight_title="Winter Tatras",
        )

        call_command("fix_parler_language_codes")

        assert translation_model.objects.filter(language_code="en-us").count() == 0
        assert astro_translation_model.objects.filter(language_code="en-us").count() == 0
        assert location_translation_model.objects.filter(language_code="en-us").count() == 0
        assert translation_model.objects.filter(language_code="en", name="Tatras").exists()
        assert astro_translation_model.objects.filter(
            language_code="en", name="Legacy Astro"
        ).exists()
        assert location_translation_model.objects.filter(language_code="en", story="Story").exists()


@pytest.mark.django_db
class TestCreateAstroImagesBatchCommand:
    def test_create_astroimages_batch_uses_default_count_and_sets_translations(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch("astrophotography.models.Place.trigger_translations", autospec=True)
        mocker.patch("astrophotography.models.AstroImage.trigger_translations", autospec=True)
        mocker.patch("core.models.process_image_task.delay_on_commit")
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )

        output = StringIO()

        call_command("create_astroimages_batch", stdout=output)

        assert AstroImage.objects.count() == 10
        first_image = AstroImage.objects.order_by("created_at").first()
        assert first_image is not None
        assert (
            first_image.safe_translation_getter("name", language_code="en") == "Batch Astro Image 1"
        )
        assert (
            first_image.safe_translation_getter("name", language_code="pl")
            == "Testowy obraz astro 1"
        )
        assert first_image.original
        assert "Created 10 AstroImage record(s)" in output.getvalue()

    def test_create_astroimages_batch_respects_count_option(self, mocker: MockerFixture) -> None:
        mocker.patch("astrophotography.models.Place.trigger_translations", autospec=True)
        mocker.patch("astrophotography.models.AstroImage.trigger_translations", autospec=True)
        mocker.patch("core.models.process_image_task.delay_on_commit")
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )

        call_command("create_astroimages_batch", count=3)

        assert AstroImage.objects.count() == 3
        names = list(
            AstroImage.objects.order_by("created_at").values_list("translations__name", flat=True)
        )
        assert any(name == "Batch Astro Image 1" for name in names)
        assert any(name == "Batch Astro Image 3" for name in names)
