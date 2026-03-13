# backend/common/tests/image_helpers.py
"""Shared test helpers for image-related tests."""
from io import BytesIO

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile


class NamedBytesIO(BytesIO):
    """BytesIO with a .name attribute for mock file handling."""

    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def _jpeg_field(name: str = "avatar.jpg", color: tuple = (10, 20, 30)) -> SimpleUploadedFile:
    """Return a SimpleUploadedFile backed by a real JPEG — PIL-compatible."""
    buf = BytesIO()
    Image.new("RGB", (10, 10), color=color).save(buf, "JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


def _png_field(name: str = "photo.png", mode: str = "RGB") -> SimpleUploadedFile:
    """Return a SimpleUploadedFile backed by a real PNG — PIL-compatible."""
    buf = BytesIO()
    Image.new(mode, (10, 10)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def _make_jpeg_bytes(size: tuple = (20, 20), color: tuple = (10, 20, 30)) -> bytes:
    """Return raw JPEG bytes."""
    buf = BytesIO()
    Image.new("RGB", size, color=color).save(buf, "JPEG")
    return buf.getvalue()
