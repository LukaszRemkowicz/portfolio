import os
import secrets
from dataclasses import dataclass
from io import BytesIO
from typing import IO, cast

from PIL import Image, UnidentifiedImageError

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.utils.deconstruct import deconstructible

from common.types import ProcessableImageFile


@dataclass(frozen=True)
class ImageOutputFormat:
    """Generated image output contract shared by encoding and file naming."""

    pillow_format: str
    extension: str
    mime_type: str


IMAGE_FORMAT = ImageOutputFormat(
    pillow_format="WEBP",
    extension=".webp",
    mime_type="image/webp",
)


def has_output_image_extension(
    file_name: str | None,
    output_format: ImageOutputFormat = IMAGE_FORMAT,
) -> bool:
    """Return whether a file name already uses the generated image extension."""
    return str(file_name or "").lower().endswith(output_format.extension)


def get_output_image_name(
    source_name: str,
    *,
    filename_prefix: str = "",
    output_format: ImageOutputFormat = IMAGE_FORMAT,
) -> str:
    """Return a seeded generated-image name using the configured output extension."""
    source_base_name = os.path.basename(source_name)
    source_stem = os.path.splitext(source_base_name)[0] or "unknown"
    return seed_file_name(f"{filename_prefix}{source_stem}{output_format.extension}")


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


def build_image_thumbnail(
    image: ProcessableImageFile, size: tuple[int, int], filename_prefix: str = "thumb_"
) -> ContentFile:
    """Build a generated-image thumbnail with the shared resizing and naming rules.

    The generated thumbnail:
    - preserves aspect ratio via Pillow's ``thumbnail()``
    - flattens transparency onto white for predictable portfolio rendering
    - uses the centralized project image format
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
    img.save(thumb_io, IMAGE_FORMAT.pillow_format, lossless=True, method=6)
    source_name = getattr(image, "name", "unknown").split("/")[-1]
    thumbnail_name = get_output_image_name(source_name, filename_prefix=filename_prefix)
    return ContentFile(thumb_io.getvalue(), name=thumbnail_name)


def build_image_with_given_width(
    image: ProcessableImageFile,
    *,
    width: int,
    quality: int,
    filename_prefix: str,
) -> tuple[ContentFile, int, int] | None:
    """Build a width-constrained generated image while preserving aspect ratio."""
    try:
        if hasattr(image, "seek"):
            image.seek(0)
        with Image.open(cast(IO[bytes], image)) as opened_image:
            img = opened_image.copy()
    except (OSError, ValueError, UnidentifiedImageError):
        return None

    img = _flatten_image_to_rgb(img)
    if img.width < width:
        return None

    height = max(1, round(img.height * (width / img.width)))
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    output = BytesIO()
    try:
        img.save(output, IMAGE_FORMAT.pillow_format, quality=quality)
    except (OSError, ValueError):
        return None

    source_name = getattr(image, "name", "unknown").split("/")[-1]
    variant_name = get_output_image_name(source_name, filename_prefix=filename_prefix)
    return ContentFile(output.getvalue(), name=variant_name), width, height


def _flatten_image_to_rgb(img: Image.Image) -> Image.Image:
    """Return an RGB image, flattening transparent pixels onto white."""
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        return bg

    if img.mode == "P" and "transparency" in img.info:
        return _flatten_image_to_rgb(img.convert("RGBA"))

    return img.convert("RGB")


def convert_to_project_image_format(
    image_field: ProcessableImageFile | None,
    quality: int = 90,
    max_dimension: int | None = None,
    dimension_percentage: int | None = None,
) -> tuple[str, ContentFile] | None:
    """Convert an open ImageField to the centralized project image format.

    Args:
        image_field: An open Django ImageFieldFile (for example ``instance.original``).
        quality: Output encoding quality (1-100). Defaults to 90.
        max_dimension: Resize proportionally so the longest side is no larger than this.
        dimension_percentage: Scale both width and height by this percentage.
            When provided, it overrides ``max_dimension``.

    Returns:
        ``(original_name, output_content_file)`` on success, or ``None`` if the
        field is empty, already in the output format, or conversion fails.

    The caller is responsible for:
    1. Persisting ``original_name`` to the legacy field.
    2. Calling ``image_field.save(output_content.name, output_content, save=False)``.
    """
    if not image_field:
        return None

    # Capture current name so callers can persist the canonical original source.
    current_name: str = str(image_field.name)

    # Do not re-compress if the file already uses the project output format.
    if has_output_image_extension(current_name):
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
        img.save(output, IMAGE_FORMAT.pillow_format, quality=quality)
        output.seek(0)

        original_filename: str = os.path.basename(current_name)
        output_filename = get_output_image_name(original_filename)
        return current_name, ContentFile(output.getvalue(), name=output_filename)

    except Exception:
        return None
