import os
import secrets
from io import BytesIO
from typing import IO, cast

from PIL import Image

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.utils.deconstruct import deconstructible

from common.types import ProcessableImageFile


def get_available_image_url(image_field: FieldFile | None) -> str:
    """Return a file URL only when the field points to an existing stored file.

    Image/file fields can retain stale names after replacements, cleanup issues, or
    partial failures. This helper centralizes the safe read path used by callers that
    want to present an image URL only when storage still confirms the file exists.
    """
    if not file_exists_in_storage(image_field):
        return ""

    if image_field is None:
        return ""

    try:
        return str(image_field.url)
    except (OSError, ValueError):
        pass

    return ""


def file_exists_in_storage(file_field: FieldFile | None) -> bool:
    """Return whether a Django file field points to a file that currently exists in storage."""
    if not file_field:
        return False

    try:
        name = str(file_field.name or "")
        return bool(name and file_field.storage.exists(name))
    except (OSError, ValueError):
        return False


def delete_file_from_storage(file_field: FieldFile | None, file_name: str) -> bool:
    """Delete ``file_name`` through the given file field storage when it still exists."""
    if not file_field or not file_name:
        return False

    try:
        if file_field.storage.exists(file_name):
            file_field.storage.delete(file_name)
            return True
    except (OSError, ValueError):
        return False

    return False


def seed_file_name(file_name: str) -> str:
    """Return a unique file name while keeping the original stem and extension."""
    base_name = os.path.basename(file_name)
    stem, ext = os.path.splitext(base_name)
    safe_stem = stem or "file"
    safe_ext = ext.lower()
    token = secrets.token_hex(6)
    return f"{safe_stem}_{token}{safe_ext}"


@deconstructible
class SeededImageUploadTo:
    """Generate unique upload paths from an instance property."""

    def __init__(self, directory_property_name: str, subdirectory: str | None = None):
        self.directory_property_name = directory_property_name
        self.subdirectory = subdirectory.strip("/") if subdirectory else None

    def __call__(self, instance, filename: str) -> str:
        directory = str(getattr(instance, self.directory_property_name)).rstrip("/")
        if self.subdirectory:
            directory = f"{directory}/{self.subdirectory}"
        return f"{directory}/{seed_file_name(filename)}"


def seeded_image_upload_to(
    directory_property_name: str, subdirectory: str | None = None
) -> SeededImageUploadTo:
    """Return a deconstructible upload_to helper that reads a directory from the instance."""
    return SeededImageUploadTo(directory_property_name, subdirectory)


def build_webp_thumbnail(
    image: ProcessableImageFile, size: tuple[int, int], filename_prefix: str = "thumb_"
) -> ContentFile:
    """Build a WebP thumbnail with the shared resizing and naming rules.

    The generated thumbnail:
    - preserves aspect ratio via Pillow's ``thumbnail()``
    - flattens transparency onto white for predictable portfolio rendering
    - uses lossless WebP for visual sharpness
    - gets a seeded file name derived from the source file name
    """
    img: Image.Image = Image.open(cast(IO[bytes], image))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    img.thumbnail(size, Image.Resampling.LANCZOS)
    thumb_io = BytesIO()
    img.save(thumb_io, "WEBP", lossless=True, method=6)
    source_name = getattr(image, "name", "unknown").split("/")[-1]
    thumbnail_name = seed_file_name(filename_prefix + os.path.splitext(source_name)[0] + ".webp")
    return ContentFile(thumb_io.getvalue(), name=thumbnail_name)


def convert_to_webp(
    image_field: ProcessableImageFile | None,
    quality: int = 90,
    max_dimension: int | None = None,
    dimension_percentage: int | None = None,
) -> tuple[str, ContentFile] | None:
    """Convert an open ImageField to WebP format.

    Args:
        image_field: An open Django ImageFieldFile (e.g. ``instance.original``).
        quality: WebP encoding quality (1–100). Defaults to 90.
        max_dimension: Resize proportionally so the longest side is no larger than this.
        dimension_percentage: Scale both width and height by this percentage.
            When provided, it overrides ``max_dimension``.

    Returns:
        ``(original_name, webp_content_file)`` on success, or ``None`` if the
        field is empty, already a ``.webp``, or conversion fails.

    The caller is responsible for:
    1. Persisting ``original_name`` to the canonical source field when needed.
    2. Calling ``image_field.save(webp_content_file.name, webp_content_file, save=False)``.
    """
    if not image_field:
        return None

    # Capture the current source name so the caller can retain the canonical upload reference.
    current_name: str = str(image_field.name)

    # Do not re-compress if the file is already a WebP image.
    if current_name.lower().endswith(".webp"):
        return None

    try:
        img: Image.Image = Image.open(cast(IO[bytes], image_field))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        if dimension_percentage is not None:
            if not 1 <= dimension_percentage <= 100:
                return None
            scaled_width = max(1, round(img.width * (dimension_percentage / 100)))
            scaled_height = max(1, round(img.height * (dimension_percentage / 100)))
            img = img.resize(
                (scaled_width, scaled_height),
                resample=Image.Resampling.LANCZOS,
            )
        elif max_dimension:
            # thumbnail() resizes the image to be no larger than the given size,
            # preserving the aspect ratio.
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        output: BytesIO = BytesIO()
        img.save(output, "WEBP", quality=quality)
        output.seek(0)

        original_filename: str = os.path.basename(current_name)
        webp_filename = seed_file_name(os.path.splitext(original_filename)[0] + ".webp")
        return current_name, ContentFile(output.getvalue(), name=webp_filename)

    except Exception:
        return None
