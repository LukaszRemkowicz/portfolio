# backend/users/tests/test_webp.py
"""Tests for WebP-related methods on the User model."""
from io import BytesIO
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from PIL import Image

from core.models import LandingPageSettings
from core.tests.factories import LandingPageSettingsFactory
from users.tests.factories import UserFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class NamedBytesIO(BytesIO):
    """BytesIO subclass that carries a filename — mirrors Django's ImageFieldFile."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name

    # Provide a no-op save() so the code under test can call field.save(...)
    def save(self, name, content, **kwargs) -> None:  # noqa: ANN001
        pass


def _jpeg_field(name: str = "avatar.jpg") -> NamedBytesIO:
    """Return a NamedBytesIO backed by a real JPEG — PIL-compatible."""
    buf = BytesIO()
    Image.new("RGB", (10, 10), color=(10, 20, 30)).save(buf, "JPEG")
    return NamedBytesIO(buf.getvalue(), name)


# ---------------------------------------------------------------------------
# User._convert_image_field_to_webp()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserConvertImageFieldToWebp:
    def test_skips_empty_field(self):
        """If the field has no image, legacy must not be set."""
        user = UserFactory.create_superuser()
        # avatar is empty by default
        user._convert_image_field_to_webp("avatar", "avatar_legacy")
        # legacy should be cleared (None), not set to a path
        assert not user.avatar_legacy

    def test_skips_already_webp(self):
        """If the field already points to .webp, legacy stays None."""
        user = UserFactory.create_superuser()
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "avatar.webp"
        user.avatar = field

        user._convert_image_field_to_webp("avatar", "avatar_legacy")
        assert not user.avatar_legacy

    def test_converts_and_sets_legacy(self):
        """A JPEG avatar should be converted; legacy_field is set to original name."""
        user = UserFactory.create_superuser()
        field = _jpeg_field("avatar.jpg")
        user.avatar = field

        user._convert_image_field_to_webp("avatar", "avatar_legacy")

        # legacy set to original filename
        assert user.avatar_legacy == "avatar.jpg"

    def test_sets_legacy_to_none_on_broken_image(self):
        """If PIL cannot open the image, legacy_field is cleared, no exception raised."""
        user = UserFactory.create_superuser()
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "broken.jpg"
        field.read.side_effect = OSError("corrupt")
        user.avatar = field

        # Should not raise
        user._convert_image_field_to_webp("avatar", "avatar_legacy")
        assert not user.avatar_legacy


# ---------------------------------------------------------------------------
# User._get_serving_image_url()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserGetServingImageUrl:
    def _user_with_mocked_fields(
        self, webp_url: str = "/media/avatar.webp", legacy_url: str = "/media/avatar.jpg"
    ):
        user = UserFactory.create_superuser()

        webp_field = MagicMock()
        webp_field.__bool__ = MagicMock(return_value=True)
        webp_field.url = webp_url

        legacy_field = MagicMock()
        legacy_field.__bool__ = MagicMock(return_value=True)
        legacy_field.url = legacy_url

        user.avatar = webp_field
        user.avatar_legacy = legacy_field
        return user

    def test_serves_webp_when_toggle_is_on(self):
        """When serve_webp_images=True, the WebP field URL is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        user = self._user_with_mocked_fields()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_legacy")

        assert url == "/media/avatar.webp"

    def test_serves_legacy_when_toggle_is_off(self):
        """When serve_webp_images=False, the legacy field URL is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        user = self._user_with_mocked_fields()

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_legacy")

        assert url == "/media/avatar.jpg"

    def test_falls_back_to_webp_when_no_legacy_and_toggle_off(self):
        """When serve_webp_images=False but legacy is empty, falls back to WebP field."""
        settings = LandingPageSettingsFactory(serve_webp_images=False)
        user = UserFactory.create_superuser()

        webp_field = MagicMock()
        webp_field.__bool__ = MagicMock(return_value=True)
        webp_field.url = "/media/avatar.webp"

        user.avatar = webp_field
        user.avatar_legacy = None  # no legacy

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_legacy")

        assert url == "/media/avatar.webp"

    def test_returns_empty_string_when_field_has_no_url(self):
        """If the serving field's .url property raises ValueError, '' is returned."""
        settings = LandingPageSettingsFactory(serve_webp_images=True)
        user = UserFactory.create_superuser()

        bad_field = MagicMock()
        bad_field.__bool__ = MagicMock(return_value=True)
        # PropertyMock makes .url raise on attribute access, not on call
        type(bad_field).url = PropertyMock(side_effect=ValueError("no file"))
        user.avatar = bad_field
        user.avatar_legacy = None

        with patch.object(LandingPageSettings, "get_current", return_value=settings):
            url = user._get_serving_image_url("avatar", "avatar_legacy")

        assert url == ""
