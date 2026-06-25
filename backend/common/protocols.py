from __future__ import annotations

from typing import Any, Protocol

from common.types import ImageVariantSource, ImageVariantSpec


class ImageVariantSyncCapable(Protocol):
    """Typing contract for models that participate in ImageVariant syncing."""

    def get_image_variant_sources(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]: ...

    def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]: ...

    def sync_image_variants(
        self,
        changed_field_names: list[str] | None = None,
        *,
        force: bool = False,
    ) -> int: ...

    def save(self, *args: Any, **kwargs: Any) -> None: ...
