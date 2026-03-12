# backend/common/tests/test_image_utils.py
"""Unit tests for common.utils.image — convert_to_webp utility."""
from io import BytesIO
from unittest.mock import MagicMock

from PIL import Image

from common.utils.image import convert_to_webp

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class NamedBytesIO(BytesIO):
    """BytesIO subclass that carries a filename — mirrors Django's ImageFieldFile."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name


def _jpeg_field(name: str = "photo.jpg") -> NamedBytesIO:
    buf = BytesIO()
    Image.new("RGB", (10, 10), color=(100, 150, 200)).save(buf, "JPEG")
    return NamedBytesIO(buf.getvalue(), name)


def _png_field(name: str = "photo.png", mode: str = "RGB") -> NamedBytesIO:
    buf = BytesIO()
    Image.new(mode, (10, 10)).save(buf, "PNG")
    return NamedBytesIO(buf.getvalue(), name)


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
        assert original_name == "images/photo.jpg"
        assert webp_content.name == "photo.webp"

        webp_content.seek(0)
        img = Image.open(webp_content)
        assert img.format == "WEBP"

    def test_output_filename_strips_original_extension(self):
        """Output filename should swap the original extension for .webp."""
        result = convert_to_webp(_png_field("uploads/banner.png"))

        assert result is not None
        _, webp_content = result
        assert webp_content.name == "banner.webp"

    def test_custom_quality_is_accepted(self):
        """A custom quality value should not raise and should produce output."""
        result = convert_to_webp(_jpeg_field(), quality=50)
        assert result is not None

    def test_rgba_png_is_converted(self):
        """An RGBA image (transparent PNG) should convert without error."""
        result = convert_to_webp(_png_field("icon.png", mode="RGBA"))
        assert result is not None
        _, webp_content = result
        webp_content.seek(0)
        assert Image.open(webp_content).format == "WEBP"
