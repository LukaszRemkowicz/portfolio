import os
from io import StringIO

import pytest
from pytest_mock import MockerFixture
from rest_framework import status

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.urls import reverse

from astrophotography.models import MeteorsMainPageConfig
from astrophotography.tests.factories import AstroImageFactory, MainPageBackgroundImageFactory
from core.models import LandingPageSettings
from programming.models import ProjectImage


@pytest.mark.django_db
class TestSeedSettingsCommand:
    def test_seed_settings_creates_defaults(self, api_client):
        """Test that seed_settings command creates default settings and config"""
        # Ensure no settings record exists
        LandingPageSettings.objects.all().delete()
        MeteorsMainPageConfig.objects.all().delete()

        # Run seeding
        call_command("seed_settings")

        # Verify through the settings API (integrative test)
        url = reverse("settings")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Defaults should be True, and meteors should be auto-linked
        assert response.data["programming"] is True
        assert response.data["contactForm"] is True
        assert response.data["travelHighlights"] is True
        assert response.data["lastimages"] is True
        assert response.data["shop"] is False
        assert response.data["meteors"]["randomShootingStars"] is True


@pytest.mark.django_db
class TestClearCacheCommand:
    def test_clear_cache_calls_backend_cache_clear(self, mocker: MockerFixture) -> None:
        mock_clear = mocker.patch("core.management.commands.clear_cache.cache.clear")

        call_command("clear_cache")

        mock_clear.assert_called_once()


@pytest.mark.django_db
class TestRegenerateThumbnailsCommand:
    def test_regenerate_thumbnails_creates_missing_thumbnails(self, mocker: MockerFixture) -> None:
        astro_image = AstroImageFactory()
        background_image = MainPageBackgroundImageFactory()
        type(astro_image).objects.filter(pk=astro_image.pk).update(thumbnail="")
        type(background_image).objects.filter(pk=background_image.pk).update(thumbnail="")
        astro_image.refresh_from_db()
        background_image.refresh_from_db()

        mocker.patch.object(ProjectImage.objects, "all", return_value=ProjectImage.objects.none())

        astro_thumb = ContentFile(b"astro-thumb", name="thumb_astro.webp")
        background_thumb = ContentFile(b"background-thumb", name="thumb_background.webp")

        mocker.patch.object(type(astro_image), "make_thumbnail", return_value=astro_thumb)
        mocker.patch.object(type(background_image), "make_thumbnail", return_value=background_thumb)

        call_command("regenerate_thumbnails")

        astro_image.refresh_from_db()
        background_image.refresh_from_db()

        assert astro_image.thumbnail
        assert os.path.basename(astro_image.thumbnail.name).startswith("thumb_")
        assert astro_image.thumbnail.name.endswith(".webp")
        assert background_image.thumbnail
        assert os.path.basename(background_image.thumbnail.name).startswith("thumb_")
        assert background_image.thumbnail.name.endswith(".webp")

    def test_regenerate_thumbnails_skips_existing_without_force(
        self, mocker: MockerFixture
    ) -> None:
        astro_image = AstroImageFactory()
        astro_image.thumbnail.save(
            "existing_thumb.webp",
            ContentFile(b"existing-thumb", name="existing_thumb.webp"),
            save=True,
        )
        mock_make_thumbnail = mocker.patch.object(type(astro_image), "make_thumbnail")
        output = StringIO()
        original_thumbnail_name = astro_image.thumbnail.name

        call_command("regenerate_thumbnails", stdout=output)

        astro_image.refresh_from_db()
        mock_make_thumbnail.assert_not_called()
        assert "Thumbnail exists" in output.getvalue()
        assert astro_image.thumbnail.name == original_thumbnail_name

    def test_regenerate_thumbnails_force_rebuilds_existing(self, mocker: MockerFixture) -> None:
        astro_image = AstroImageFactory()
        astro_image.thumbnail.save(
            "existing_thumb.webp",
            ContentFile(b"existing-thumb", name="existing_thumb.webp"),
            save=True,
        )
        regenerated_thumb = ContentFile(b"regenerated-thumb", name="regenerated_thumb.webp")
        mocker.patch.object(type(astro_image), "make_thumbnail", return_value=regenerated_thumb)

        call_command("regenerate_thumbnails", force=True)

        astro_image.refresh_from_db()
        assert os.path.basename(astro_image.thumbnail.name).startswith("regenerated_thumb")
        assert astro_image.thumbnail.name.endswith(".webp")
