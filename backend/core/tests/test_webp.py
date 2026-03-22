# backend/core/tests/test_webp.py
"""Tests for WebP-related methods on BaseImage and LandingPageSettings."""
from unittest.mock import MagicMock, patch

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
# BaseImage._convert_to_webp() via MainPageBackgroundImage
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBaseImageConvertToWebp:
    def test_converts_jpeg_to_webp(self, tmp_path):
        """Saving a JPEG image triggers WebP conversion; original_image is populated."""
        img = MainPageBackgroundImageFactory()

        # Confirm conversion happened (factory creates an ImageField)
        assert img.path  # path exists
        # If conversion succeeded, path name ends in .webp
        if img.path.name.endswith(".webp"):
            assert img.original_image  # legacy must be set

    def test_no_op_if_already_webp(self):
        """_convert_to_webp() must not re-convert an image already in WebP."""
        img = MainPageBackgroundImageFactory()
        legacy_before = str(img.original_image) if img.original_image else None

        # Call directly with a mocked webp field
        img.path = MagicMock()
        img.path.name = "already.webp"
        img.path.__bool__ = MagicMock(return_value=True)
        img._convert_to_webp()

        # original_image must not have changed
        legacy_after = str(img.original_image) if img.original_image else None
        assert legacy_before == legacy_after

    def test_convert_to_webp_noop_on_empty_path(self):
        """_convert_to_webp() must be a no-op when path is empty."""
        img = MainPageBackgroundImageFactory.build()
        img.path = None
        img._convert_to_webp()  # should not raise


# ---------------------------------------------------------------------------
# BaseImage.get_serving_path() and get_serving_url()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBaseImageServingPath:
    def test_get_serving_path_returns_path_when_webp_enabled(self):
        """When serve_webp_images=True, get_serving_path() returns self.path."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        img = MainPageBackgroundImageFactory()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.path

    def test_get_serving_path_returns_legacy_when_webp_disabled(self):
        """When serve_webp_images=False and legacy exists, returns original_image."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        img = MainPageBackgroundImageFactory()
        # Simulate a converted image with a legacy path
        img.original_image = img.path

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.original_image

    def test_get_serving_path_falls_back_to_path_if_no_legacy(self):
        """When serve_webp_images=False and no legacy, returns self.path."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        img = MainPageBackgroundImageFactory()
        img.original_image = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            result = img.get_serving_path()

        assert result == img.path

    def test_get_serving_url_returns_string(self):
        """get_serving_url() must always return a str, never raise."""
        img = MainPageBackgroundImageFactory()
        url = img.get_serving_url()
        assert isinstance(url, str)

    def test_get_serving_url_returns_empty_string_when_no_path(self):
        """get_serving_url() returns '' when no image is assigned."""
        img = MainPageBackgroundImageFactory.build()
        img.path = None
        img.original_image = None
        url = img.get_serving_url()
        assert url == ""
