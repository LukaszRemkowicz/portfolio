# backend/common/tests/test_image_utils.py
"""Unit tests for common.utils.image helpers."""

from unittest.mock import MagicMock

import pytest
from PIL import Image

from common.tests.image_helpers import NamedBytesIO, _jpeg_field, _png_field
from common.utils import image as image_utils
from common.utils.image import (
    IMAGE_FORMAT,
    build_image_thumbnail,
    build_image_with_given_width,
    convert_to_project_image_format,
    delete_file_from_storage,
    get_output_image_name,
    has_output_image_extension,
    seed_file_name,
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestImageOutputFormat:
    """Tests for the centralized generated-image output contract."""

    def test_webp_output_contract_groups_encoder_extension_and_mime_type(self):
        assert IMAGE_FORMAT.pillow_format == "WEBP"
        assert IMAGE_FORMAT.extension == ".webp"
        assert IMAGE_FORMAT.mime_type == "image/webp"

    def test_has_output_image_extension_is_case_insensitive(self):
        assert has_output_image_extension("images/photo.webp") is True
        assert has_output_image_extension("images/photo.WEBP") is True
        assert has_output_image_extension("images/photo.jpg") is False

    def test_get_output_image_name_replaces_source_extension_and_seeds_name(self):
        output_name = get_output_image_name("uploads/photo.jpg", filename_prefix="card_560_")

        assert output_name.startswith("card_560_photo_")
        assert output_name.endswith(IMAGE_FORMAT.extension)


class TestConvertToWebp:
    """Tests for convert_to_project_image_format()."""

    # --- guard cases ---

    def test_returns_none_for_none(self):
        """None passed directly should return None."""
        assert convert_to_project_image_format(None) is None

    def test_returns_none_for_empty_mock(self):
        """A falsy ImageFieldFile (no file uploaded) should return None."""
        empty = MagicMock()
        empty.__bool__ = MagicMock(return_value=False)
        assert convert_to_project_image_format(empty) is None

    def test_returns_none_if_already_webp(self):
        """If the field name ends in .webp, no conversion occurs."""
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "images/photo.webp"
        assert convert_to_project_image_format(field) is None

    def test_returns_none_if_already_webp_uppercase(self):
        """Extension check must be case-insensitive."""
        field = MagicMock()
        field.__bool__ = MagicMock(return_value=True)
        field.name = "images/photo.WEBP"
        assert convert_to_project_image_format(field) is None

    def test_returns_none_on_broken_image(self):
        """An unreadable field should return None — no exception propagated."""
        bad = NamedBytesIO(b"not-an-image", "broken.jpg")
        assert convert_to_project_image_format(bad) is None

    # --- successful conversions ---

    def test_successful_jpeg_conversion(self):
        """A valid JPEG should return (original_name, ContentFile)."""
        result = convert_to_project_image_format(_jpeg_field("images/photo.jpg"))

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
        result = convert_to_project_image_format(_png_field("uploads/banner.png"))

        assert result is not None
        _, webp_content = result
        assert webp_content.name.startswith("banner_")
        assert webp_content.name.endswith(".webp")

    def test_custom_quality_is_accepted(self):
        """A custom quality value should not raise and should produce output."""
        result = convert_to_project_image_format(_jpeg_field(), quality=50)
        assert result is not None

    def test_dimension_percentage_scales_from_original_size(self):
        """A percentage should scale width and height directly from the original image."""
        result = convert_to_project_image_format(
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
        result = convert_to_project_image_format(
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
        result = convert_to_project_image_format(_png_field("icon.png", mode="RGBA"))
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


class TestBuildImageThumbnail:
    """Tests for build_image_thumbnail()."""

    def test_builds_seeded_webp_thumbnail(self):
        thumbnail = build_image_thumbnail(
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
        thumbnail = build_image_thumbnail(
            _png_field("images/icon.png", mode="RGBA", size=(300, 300)),
            size=(150, 150),
        )

        thumbnail.seek(0)
        image = Image.open(thumbnail)
        assert image.mode == "RGB"


class TestBuildImageWithGivenWidth:
    """Tests for build_image_with_given_width()."""

    def test_builds_webp_at_requested_width(self):
        result = build_image_with_given_width(
            _jpeg_field("images/photo.jpg", size=(1200, 800)),
            width=560,
            quality=90,
            filename_prefix="card_560_",
        )

        assert result is not None
        content, width, height = result
        assert width == 560
        assert height == 373
        assert content.name.startswith("card_560_photo_")
        assert content.name.endswith(".webp")

        content.seek(0)
        image = Image.open(content)
        assert image.format == "WEBP"
        assert image.size == (560, 373)

    def test_returns_none_for_unreadable_image(self):
        result = build_image_with_given_width(
            NamedBytesIO(b"not-an-image", "broken.jpg"),
            width=560,
            quality=90,
            filename_prefix="card_560_",
        )

        assert result is None

    def test_does_not_swallow_unexpected_runtime_errors(self, mocker):
        mocker.patch.object(image_utils, "seed_file_name", side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            build_image_with_given_width(
                _jpeg_field("images/photo.jpg", size=(1200, 800)),
                width=560,
                quality=90,
                filename_prefix="card_560_",
            )


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
