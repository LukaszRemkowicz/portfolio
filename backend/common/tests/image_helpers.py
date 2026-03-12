# backend/common/tests/image_helpers.py
"""Shared test helpers for image-related tests."""
from io import BytesIO

from PIL import Image


class NamedBytesIO(BytesIO):
    """BytesIO subclass that carries a filename — mirrors Django's ImageFieldFile."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name

    # Provide a no-op save() so the code under test can call field.save(...)
    def save(self, name, content, **kwargs) -> None:  # noqa: ANN001
        pass


def _jpeg_field(name: str = "avatar.jpg", color: tuple = (10, 20, 30)) -> NamedBytesIO:
    """Return a NamedBytesIO backed by a real JPEG — PIL-compatible."""
    buf = BytesIO()
    Image.new("RGB", (10, 10), color=color).save(buf, "JPEG")
    return NamedBytesIO(buf.getvalue(), name)


def _png_field(name: str = "photo.png", mode: str = "RGB") -> NamedBytesIO:
    """Return a NamedBytesIO backed by a real PNG — PIL-compatible."""
    buf = BytesIO()
    Image.new(mode, (10, 10)).save(buf, "PNG")
    return NamedBytesIO(buf.getvalue(), name)


def _make_jpeg_bytes(size: tuple = (20, 20), color: tuple = (10, 20, 30)) -> bytes:
    """Return raw JPEG bytes."""
    buf = BytesIO()
    Image.new("RGB", size, color=color).save(buf, "JPEG")
    return buf.getvalue()
