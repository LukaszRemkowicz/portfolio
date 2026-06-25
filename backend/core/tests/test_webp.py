# backend/core/tests/test_webp.py
"""Tests for generated-serving methods on BaseImage and LandingPageSettings."""

from unittest.mock import patch

import pytest

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from common.tests.image_helpers import jpeg_field
from core.models import LandingPageSettings
from core.tasks import process_image_task
from core.tests.factories import LandingPageSettingsFactory

# ---------------------------------------------------------------------------
# LandingPageSettings.get_current()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLandingPageSettingsGetCurrent:
    def test_returns_none_when_no_settings_exist(self):
        """get_current() must return None when the table is empty."""
        assert LandingPageSettings.get_current() is None

    def test_returns_settings_when_exists(self):
        """get_current() returns the single LandingPageSettings row."""
        settings = LandingPageSettingsFactory()
        result = LandingPageSettings.get_current()
        assert result is not None
        assert result.pk == settings.pk


# ---------------------------------------------------------------------------
# BaseImage image URL helpers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBaseImageImageUrls:
    def test_get_variant_url_returns_hero_variant_url(self):
        """Variant helper returns the generated hero URL without fallback."""
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background.jpg", size=(2600, 1734))
            )
        process_image_task("astrophotography", "MainPageBackgroundImage", img.pk)
        img.refresh_from_db()
        hero = img.variants.get(role="hero", width=2560)

        assert hero.width == 2560
        assert img.get_variant_url("hero", width=2560) == hero.file.url

    def test_get_variant_url_returns_empty_string_when_variant_missing(self):
        """Variant helper stays strict when the requested role is absent."""
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background.jpg", size=(2600, 1734))
            )
        img.variants.all().delete()

        assert img.get_variant_url("hero", width=2600) is None

    def test_get_original_image_url_returns_original_source_url(self):
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background.jpg", size=(2600, 1734))
            )

        assert img.get_original_image_url() == img.original.url

    def test_get_image_url_falls_back_to_original_when_variant_missing(self, caplog):
        """Connector falls back to the stored original file and logs a warning."""
        with patch("core.models.process_image_task.delay_on_commit"):
            img = MainPageBackgroundImageFactory(
                original=jpeg_field("background.jpg", size=(2600, 1734))
            )
        img.variants.all().delete()

        assert img.get_image_url("hero", width=2600) == img.original.url
        assert "Falling back to original source image" in caplog.text

    def test_get_image_url_returns_string(self):
        """Connector must always return a str, never raise."""
        img = MainPageBackgroundImageFactory()
        url = img.get_image_url("hero", width=img.original.width)
        assert isinstance(url, str)

    def test_get_image_url_returns_none_when_no_path(self):
        """Connector returns None when neither variant nor original exists."""
        img = MainPageBackgroundImageFactory.build()
        img.original = None
        url = img.get_image_url("hero", width=2600)
        assert url is None

    def test_get_image_url_logs_error_when_variant_and_original_are_missing(self, caplog):
        img = MainPageBackgroundImageFactory.build()
        img.original = None

        assert img.get_image_url("hero", width=2600) is None
        assert "Image variant is missing and original source image is unavailable" in caplog.text
