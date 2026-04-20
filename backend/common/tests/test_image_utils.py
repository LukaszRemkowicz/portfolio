# backend/common/tests/test_image_utils.py
"""Unit tests for common.utils.image helpers."""

from unittest.mock import MagicMock

from PIL import Image

from common.tests.image_helpers import NamedBytesIO, _jpeg_field, _png_field
from common.utils.image import (
    build_webp_thumbnail,
    convert_to_webp,
    delete_file_from_storage,
    seed_file_name,
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConvertToWebp:
    """Tests for convert_to_webp()."""

    # --- guard cases ---

    def test_returns_none_for_none(self):
        """None passed directly should return None."""
        assert convert_to_webp(None) is None

    def test_returns_none_for_empty_mock(self):
        """A falsy ImageFieldFile (no file uploaded) should return None."""
        empty = MagicMock()
        empty.__bool__ = MagicMock(return_value=False)
        assert convert_to_webp(empty) is None

    def test_returns_none_if_already_webp(self):
        """If the field name ends in .webp, no conversion occurs."""
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "images/photo.webp"
        assert convert_to_webp(field) is None

    def test_returns_none_if_already_webp_uppercase(self):
        """Extension check must be case-insensitive."""
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "images/photo.WEBP"
        assert convert_to_webp(field) is None

    def test_returns_none_on_broken_image(self):
        """An unreadable field should return None — no exception propagated."""
        bad = NamedBytesIO(b"not-an-image", "broken.jpg")
        assert convert_to_webp(bad) is None

    # --- successful conversions ---

    def test_successful_jpeg_conversion(self):
        """A valid JPEG should return (original_name, ContentFile)."""
        result = convert_to_webp(_jpeg_field("images/photo.jpg"))

        assert result is not None
        original_name, webp_content = result
        assert original_name == "photo.jpg"
        assert webp_content.name.startswith("photo_")
        assert webp_content.name.endswith(".webp")

        webp_content.seek(0)
        img = Image.open(webp_content)
        assert img.format == "WEBP"

    def test_output_filename_strips_original_extension(self):
        """Output filename should swap the original extension for .webp."""
        result = convert_to_webp(_png_field("uploads/banner.png"))

        assert result is not None
        _, webp_content = result
        assert webp_content.name.startswith("banner_")
        assert webp_content.name.endswith(".webp")

    def test_custom_quality_is_accepted(self):
        """A custom quality value should not raise and should produce output."""
        result = convert_to_webp(_jpeg_field(), quality=50)
        assert result is not None

    def test_dimension_percentage_scales_from_original_size(self):
        """A percentage should scale width and height directly from the original image."""
        result = convert_to_webp(
            _jpeg_field("images/large-photo.jpg", size=(2000, 2000)),
            dimension_percentage=50,
        )

        assert result is not None
        _, webp_content = result
        webp_content.seek(0)
        img = Image.open(webp_content)
        assert img.size == (1000, 1000)

    def test_dimension_percentage_overrides_max_dimension(self):
        """Percentage scaling should take precedence over max_dimension when both are set."""
        result = convert_to_webp(
            _jpeg_field("images/large-photo.jpg", size=(2000, 2000)),
            max_dimension=1200,
            dimension_percentage=50,
        )

        assert result is not None
        _, webp_content = result
        webp_content.seek(0)
        img = Image.open(webp_content)
        assert img.size == (1000, 1000)

    def test_rgba_png_is_converted(self):
        """An RGBA image (transparent PNG) should convert without error."""
        result = convert_to_webp(_png_field("icon.png", mode="RGBA"))
        assert result is not None
        _, webp_content = result
        webp_content.seek(0)
        img = Image.open(webp_content)
        assert img.format == "WEBP"


class TestDeleteFileFromStorage:
    """Tests for delete_file_from_storage()."""

    def test_returns_false_for_empty_input(self):
        assert delete_file_from_storage(None, "images/photo.jpg") is False
        assert delete_file_from_storage(MagicMock(), "") is False

    def test_deletes_existing_file(self):
        field = MagicMock()
        field.storage.exists.return_value = True

        result = delete_file_from_storage(field, "images/photo.jpg")

        assert result is True
        field.storage.exists.assert_called_once_with("images/photo.jpg")
        field.storage.delete.assert_called_once_with("images/photo.jpg")

    def test_skips_missing_file(self):
        field = MagicMock()
        field.storage.exists.return_value = False

        result = delete_file_from_storage(field, "images/photo.jpg")

        assert result is False
        field.storage.exists.assert_called_once_with("images/photo.jpg")
        field.storage.delete.assert_not_called()

    def test_returns_false_when_storage_check_fails(self):
        field = MagicMock()
        field.storage.exists.side_effect = OSError("boom")

        result = delete_file_from_storage(field, "images/photo.jpg")

        assert result is False
        field.storage.delete.assert_not_called()


class TestBuildWebpThumbnail:
    """Tests for build_webp_thumbnail()."""

    def test_builds_seeded_webp_thumbnail(self):
        thumbnail = build_webp_thumbnail(
            _jpeg_field("images/photo.jpg", size=(1600, 1200)),
            size=(400, 400),
        )

        assert thumbnail.name.startswith("thumb_photo_")
        assert thumbnail.name.endswith(".webp")

        thumbnail.seek(0)
        image = Image.open(thumbnail)
        assert image.format == "WEBP"
        assert image.width <= 400
        assert image.height <= 400

    def test_flattens_transparent_png_to_rgb(self):
        thumbnail = build_webp_thumbnail(
            _png_field("images/icon.png", mode="RGBA", size=(300, 300)),
            size=(150, 150),
        )

        thumbnail.seek(0)
        image = Image.open(thumbnail)
        assert image.mode == "RGB"


class TestSeedFileName:
    """Tests for seed_file_name()."""

    def test_keeps_stem_and_extension(self):
        seeded_name = seed_file_name("photo.JPG")

        assert seeded_name.startswith("photo_")
        assert seeded_name.endswith(".jpg")

    def test_generates_different_names_for_same_input(self):
        first_name = seed_file_name("photo.jpg")
        second_name = seed_file_name("photo.jpg")

        assert first_name != second_name
