"""Image processing utilities shared across all apps."""

import os
from io import BytesIO
from typing import Any

from PIL import Image

from django.core.files.base import ContentFile


def convert_to_webp(
    image_field: Any,
    quality: int = 90,
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

    current_name: str = str(image_field.name)
    if current_name.lower().endswith(".webp"):
        return None

    try:
        img: Any = Image.open(image_field)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        output: BytesIO = BytesIO()
        img.save(output, "WEBP", quality=quality)
        output.seek(0)

        original_filename: str = os.path.basename(current_name)
        webp_filename: str = os.path.splitext(original_filename)[0] + ".webp"
        return current_name, ContentFile(output.getvalue(), name=webp_filename)

    except Exception:
        return None
