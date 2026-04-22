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
