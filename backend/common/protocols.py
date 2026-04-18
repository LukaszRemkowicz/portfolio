from __future__ import annotations

from typing import Any, Protocol

from common.types import ImageProcessingOperation


class ImageProcessingCapable(Protocol):
    """Typing contract for models that participate in shared image processing."""

    def get_image_processing_operations(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageProcessingOperation]: ...

    def save(self, *args: Any, **kwargs: Any) -> None: ...
