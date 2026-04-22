from __future__ import annotations

from typing import Any, Protocol

from django import forms


class AstroImageExposureTimeExtractor(Protocol):
    """Contract for services that can extract exposure hours from normalized text."""

    def extract_total_hours(self, normalized_exposure_details: str) -> str | None: ...


class SupportsBaseImageUploadForm(Protocol):
    """Typing contract for admin forms using the BaseImage source-upload mixin."""

    fields: dict[str, forms.Field]
    instance: Any
    cleaned_data: dict[str, Any]

    def add_error(self, field: str | None, error: Any) -> None: ...
    def _get_current_source_field(self) -> Any: ...
    def _init_secure_original_widget(self, current_source: Any) -> None: ...
