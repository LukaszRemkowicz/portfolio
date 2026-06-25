from __future__ import annotations

from dataclasses import dataclass
from typing import IO

from django.db.models.fields.files import FieldFile, ImageFieldFile


@dataclass(frozen=True)
class ImageSpec:
    """Configuration for image optimization."""

    dimension: int
    quality: int
    dimension_percentage: int | None = None
    aspect_ratio: float | None = None


@dataclass(frozen=True)
class ViewportWidths:
    """Target generated image widths for each public responsive viewport."""

    mobile: int
    tablet: int
    desktop: int
    wide: int

    @classmethod
    def fixed(cls, width: int) -> ViewportWidths:
        """Return one generated width shared by every viewport."""
        return cls(
            mobile=width,
            tablet=width,
            desktop=width,
            wide=width,
        )

    def as_tuple(self) -> tuple[int, ...]:
        """Return deduplicated widths in mobile-to-wide order."""
        return tuple(dict.fromkeys((self.mobile, self.tablet, self.desktop, self.wide)))


@dataclass(frozen=True)
class ImageVariantSpec:
    """Configuration for one generated image variant role.

    A spec describes how to create one family of generated image files from the
    uploaded source image.

    Attributes:
        role: Stable machine-readable display role, such as ``card``,
            ``detail``, ``hero``, or ``original_format``. The role is stored on
            ``ImageVariant.role`` and used by lookup APIs.
        viewport_widths: Target generated image widths for each supported
            frontend viewport bucket. Height is calculated from source aspect
            ratio.
        quality: Encoding quality passed to the project image format encoder.
        label: Human-readable description for admins, docs, logs, and future
            maintainers. It is not used as a lookup key.
    """

    role: str
    viewport_widths: ViewportWidths
    quality: int
    label: str = ""

    def target_widths_for_source(
        self, source_width: int, *, required: bool = False
    ) -> tuple[int, ...]:
        """Return target widths supported by the source image width."""
        configured_widths = self.viewport_widths.as_tuple()
        widths = tuple(width for width in configured_widths if width <= source_width)
        if not widths and required and configured_widths:
            return (source_width,)
        return widths


type ProcessableImageFile = IO[bytes] | FieldFile


@dataclass(frozen=True)
class ImageVariantSource:
    """Describe one original/source image family used to generate variants.

    This is source metadata, not a generated variant. The model provides one
    object per source file family; ``ImageVariantModelMixin`` combines it with
    ``ImageVariantSpec`` entries to create concrete role/width rows.
    """

    field_name: str
    source_image: ImageFieldFile | None
    upload_dir: str
    role_namespace: str | None = None
