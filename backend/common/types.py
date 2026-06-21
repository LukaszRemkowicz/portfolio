from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import IO

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile


@dataclass(frozen=True)
class ImageSpec:
    """Configuration for image optimization."""

    dimension: int
    quality: int
    dimension_percentage: int | None = None
    aspect_ratio: float | None = None


@dataclass(frozen=True)
class ImageVariantSpec:
    """Configuration for one generated image variant role.

    A spec describes how to create one family of generated image files from the
    uploaded source image.

    Attributes:
        role: Stable machine-readable display role, such as ``card``,
            ``detail``, ``hero``, or ``original_format``. The role is stored on
            ``ImageVariant.role`` and used by lookup APIs.
        widths: Target output widths in pixels. One ``ImageVariant`` row and
            file is generated for each width that is not larger than the source
            image width. Height is calculated from the source aspect ratio.
            Example: ``widths=(320, 560)`` for a ``3000x2000`` source creates
            roughly ``320x213`` and ``560x373`` variants.
        quality: Encoding quality passed to the project image format encoder.
            The current project ``IMAGE_FORMAT`` is WebP, so this is WebP
            quality today.
        label: Human-readable description for admins, docs, logs, and future
            maintainers. It is not used as a lookup key.
    """

    role: str
    widths: tuple[int, ...]
    quality: int
    label: str


type ProcessableImageFile = IO[bytes] | FieldFile


@dataclass(frozen=True)
class ImageProcessingOperation:
    """Describe one image-processing step for a model field family."""

    field_name: str
    source_image: ProcessableImageFile | None
    webp_field_name: str
    spec: ImageSpec
    original_field_name: str | None = None
    thumbnail_field_name: str | None = None
    thumbnail_source_image: ProcessableImageFile | None = None
    thumbnail_generator: Callable[[ProcessableImageFile], ContentFile] | None = None
    clear_field_on_missing_source: bool = True
    clear_field_on_failed_conversion: bool = False
