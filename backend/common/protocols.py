from __future__ import annotations

from typing import Any, Protocol

from django.db import models

from common.types import ImageProcessingOperation


class ImageProcessingCapable(Protocol):
    """Typing contract for models that participate in shared image processing."""

    def get_image_processing_operations(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageProcessingOperation]: ...

    def generate_image_variants_or_none(
        self, *, force: bool = False
    ) -> models.QuerySet[Any] | None: ...

    def save(self, *args: Any, **kwargs: Any) -> None: ...
