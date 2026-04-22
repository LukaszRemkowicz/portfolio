# backend/core/tests/test_webp.py
"""Tests for WebP-related methods on BaseImage and LandingPageSettings."""

from unittest.mock import patch

import pytest

from astrophotography.tests.factories import MainPageBackgroundImageFactory
from core.models import LandingPageSettings
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

    def test_returns_false_for_serve_webp_images_by_default(self):
        """serve_webp_images defaults to False on a fresh settings object."""
        settings = LandingPageSettingsFactory()
        assert settings.serve_webp_images is False


# ---------------------------------------------------------------------------
# BaseImage.get_serving_path() and get_serving_url()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBaseImageServingPath:
    def test_get_serving_path_returns_original_webp_when_webp_enabled(self):
        """When serve_webp_images=True, get_serving_path() returns original_webp."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        img = MainPageBackgroundImageFactory()
        img.original_webp = "images/example.webp"

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.original_webp

    def test_get_serving_path_returns_original_when_webp_disabled(self):
        """When serve_webp_images=False, get_serving_path() returns original."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        img = MainPageBackgroundImageFactory()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.original

    def test_get_serving_path_returns_original_when_webp_enabled_but_missing(self):
        """When WebP serving is enabled but no WebP exists, use the canonical original."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        img = MainPageBackgroundImageFactory()
        img.original_webp = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.original

    def test_get_serving_path_returns_none_without_canonical_fields(self):
        """When canonical fields are missing, get_serving_path() returns None."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        img = MainPageBackgroundImageFactory.build()
        img.original = None
        img.original_webp = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert not result

    def test_get_serving_url_returns_string(self):
        """get_serving_url() must always return a str, never raise."""
        img = MainPageBackgroundImageFactory()
        url = img.get_serving_url()
        assert isinstance(url, str)

    def test_get_serving_url_returns_empty_string_when_no_path(self):
        """get_serving_url() returns '' when no image is assigned."""
        img = MainPageBackgroundImageFactory.build()
        img.original = None
        img.original_webp = None
        url = img.get_serving_url()
        assert url == ""
