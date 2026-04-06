from typing import Protocol


class AstroImageExposureTimeExtractor(Protocol):
    """Contract for services that can extract exposure hours from normalized text."""

    def extract_total_hours(self, normalized_exposure_details: str) -> str | None: ...
