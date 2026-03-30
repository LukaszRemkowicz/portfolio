# backend/users/tests/test_webp.py
"""Tests for WebP-related methods on the User model."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from common.tests.image_helpers import _jpeg_field
from core.models import LandingPageSettings
from core.tests.factories import LandingPageSettingsFactory
from users.tests.factories import UserFactory

# ---------------------------------------------------------------------------
# User._convert_image_field_to_webp()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserConvertImageFieldToWebp:
    def test_uses_cropped_image_when_present(self):
        """If a cropped image exists, the derived WebP should be generated from it."""
        user = UserFactory.create_superuser()
        user.avatar = _jpeg_field("avatar-original.jpg")
        user.avatar_cropped = _jpeg_field("avatar-cropped.jpg")

        user._convert_image_field_to_webp("avatar", "avatar_webp", 1000, 80)

        assert str(user.avatar_webp.name).endswith(".webp")
        assert "avatar-cropped" in str(user.avatar_webp.name)

    def test_skips_empty_field(self):
        """If the source field has no image, the derived WebP field must stay empty."""
        user = UserFactory.create_superuser()
        user._convert_image_field_to_webp("avatar", "avatar_webp", 1000, 80)
        assert not user.avatar_webp

    def test_skips_already_webp(self):
        """If the source already points to .webp, the derived field mirrors it."""
        user = UserFactory.create_superuser()
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "avatar.webp"
        user.avatar = field

        user._convert_image_field_to_webp("avatar", "avatar_webp", 1000, 80)
        assert user.avatar_webp == "avatar.webp"

    def test_converts_and_sets_webp_field(self):
        """A JPEG avatar should be converted into the derived WebP field."""
        user = UserFactory.create_superuser()
        field = _jpeg_field("avatar.jpg")
        user.avatar = field

        user._convert_image_field_to_webp("avatar", "avatar_webp", 1000, 80)

        assert str(user.avatar_webp.name).endswith(".webp")

    def test_sets_webp_field_to_none_on_broken_image(self):
        """If PIL cannot open the image, the derived field is cleared, no exception raised."""
        user = UserFactory.create_superuser()
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "broken.jpg"
        field.read.side_effect = OSError("corrupt")
        user.avatar = field

        user._convert_image_field_to_webp("avatar", "avatar_webp", 1000, 80)
        assert not user.avatar_webp


# ---------------------------------------------------------------------------
# User._get_serving_image_url()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserGetServingImageUrl:
    def _user_with_mocked_fields(
        self, webp_url: str = "/media/avatar.webp", source_url: str = "/media/avatar.jpg"
    ):
        user = UserFactory.create_superuser()

        webp_field = MagicMock()
        webp_field.__bool__ = MagicMock(return_value=True)
        webp_field.url = webp_url

        source_field = MagicMock()
        source_field.__bool__ = MagicMock(return_value=True)
        source_field.url = source_url

        user.avatar = source_field
        user.avatar_webp = webp_field
        return user

    def test_serves_webp_when_toggle_is_on(self):
        """When serve_webp_images=True, the WebP field URL is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        user = self._user_with_mocked_fields()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_webp")

        assert url == "/media/avatar.webp"

    def test_serves_source_when_toggle_is_off(self):
        """When serve_webp_images=False, the source field URL is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        user = self._user_with_mocked_fields()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_webp")

        assert url == "/media/avatar.jpg"

    def test_falls_back_to_source_when_no_webp_and_toggle_on(self):
        """When serve_webp_images=True but no WebP exists, falls back to the source field."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        user = UserFactory.create_superuser()

        source_field = MagicMock()
        source_field.__bool__ = MagicMock(return_value=True)
        source_field.url = "/media/avatar.jpg"

        user.avatar = source_field
        user.avatar_webp = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_webp")

        assert url == "/media/avatar.jpg"

    def test_prefers_cropped_source_when_webp_toggle_is_off(self):
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        user = UserFactory.create_superuser()

        source_field = MagicMock()
        source_field.__bool__ = MagicMock(return_value=True)
        source_field.url = "/media/avatar-original.jpg"

        cropped_field = MagicMock()
        cropped_field.__bool__ = MagicMock(return_value=True)
        cropped_field.url = "/media/avatar-cropped.jpg"

        user.avatar = source_field
        user.avatar_cropped = cropped_field
        user.avatar_webp = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_webp")

        assert url == "/media/avatar-cropped.jpg"

    def test_returns_empty_string_when_field_has_no_url(self):
        """If the serving field's .url property raises ValueError, '' is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        user = UserFactory.create_superuser()

        bad_field = MagicMock()
        bad_field.__bool__ = MagicMock(return_value=True)
        type(bad_field).url = PropertyMock(side_effect=ValueError("no file"))
        user.avatar = bad_field
        user.avatar_webp = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_webp")

        assert url == ""
