import os
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image

from django.core.files.base import ContentFile


@dataclass(frozen=True)
class ImageSpec:
    """Configuration for image optimization."""

    dimension: int
    quality: int


def convert_to_webp(
    image_field: Any,
    quality: int = 90,
    max_dimension: int | None = None,
) -> tuple[str, ContentFile] | None:
    """Convert an open ImageField to WebP format.

    Args:
        image_field: An open Django ImageFieldFile (e.g. ``instance.path``).
        quality: WebP encoding quality (1–100). Defaults to 90.

    Returns:
        ``(original_name, webp_content_file)`` on success, or ``None`` if the
        field is empty, already a ``.webp``, or conversion fails.

    The caller is responsible for:
    1. Persisting ``original_name`` to the legacy field.
    2. Calling ``image_field.save(webp_content_file.name, webp_content_file, save=False)``.
    """
    if not image_field:
        return None

    # Capture current name to return as 'original_name' (legacy_path) for rollbacks.
    current_name: str = str(image_field.name)

    # Do not re-compress if the file is already a WebP image.
    if current_name.lower().endswith(".webp"):
        return None

    try:
        img: Any = Image.open(image_field)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Proportional resizing if max_dimension is set
        if max_dimension:
            # thumbnail() resizes the image to be no larger than the given size,
            # preserving the aspect ratio.
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        output: BytesIO = BytesIO()
        img.save(output, "WEBP", quality=quality)
        output.seek(0)

        original_filename: str = os.path.basename(current_name)
        webp_filename: str = os.path.splitext(original_filename)[0] + ".webp"
        return current_name, ContentFile(output.getvalue(), name=webp_filename)

    except Exception:
        return None
