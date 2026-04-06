from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from django.conf import settings

from common.llm.protocols import LLMProvider
from common.llm.providers import MockLLMProvider
from common.llm.registry import LLMProviderRegistry

from .agent import AstroImageExposureTimeAgent
from .protocols import AstroImageExposureTimeExtractor

if TYPE_CHECKING:
    from .models import AstroImage


class AstroImageExposureTimeService:
    """Parse one AstroImage exposure-details string into decimal hours."""

    def __init__(self, extractor: AstroImageExposureTimeExtractor) -> None:
        self.extractor: AstroImageExposureTimeExtractor = extractor

    @classmethod
    def create_default(cls) -> AstroImageExposureTimeService:
        """Build the service with the default extraction strategy."""
        extractor: AstroImageExposureTimeExtractor = (
            AstroImageExposureTimeAgentService.create_default()
        )
        return cls(extractor=extractor)

    def parse_extracted_total_hours(self, raw_value: str | None) -> float:
        """Validate a raw extracted hours value and return the stored float."""
        if not raw_value:
            raise ValueError("Landing page total time spent response was empty.")

        return self._parse_response_value(raw_value)

    def get_exposure_details(self, astro_image: AstroImage) -> str:
        """Read the default-language exposure details for one AstroImage."""
        exposure_details: str = str(
            astro_image.safe_translation_getter(
                "exposure_details",
                language_code=settings.DEFAULT_APP_LANGUAGE,
                any_language=False,
            )
            or astro_image.safe_translation_getter("exposure_details", any_language=True)
            or ""
        )
        return exposure_details

    def parse_total_hours(self, exposure_details: str) -> float:
        """Normalize exposure text, run the configured extractor, and validate the response."""
        normalized_value: str = self.normalize_exposure_details(exposure_details)
        if not normalized_value:
            return 0.0

        raw_value: str | None = self.extractor.extract_total_hours(normalized_value)
        return self.parse_extracted_total_hours(raw_value)

    @staticmethod
    def normalize_exposure_details(raw_value: str) -> str:
        """Convert HTML-rich exposure text into a compact plain-text string."""
        soup: BeautifulSoup = BeautifulSoup(raw_value, "html.parser")
        text: str = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _parse_response_value(raw_text: str) -> float:
        """Validate the LLM output as a non-negative float rounded to two decimals."""
        value: str = raw_text.strip()
        try:
            parsed: float = float(value)
        except ValueError as exc:
            raise ValueError(
                "Landing page total time spent response must be a single number."
            ) from exc
        if parsed < 0:
            raise ValueError("Landing page total time spent response cannot be negative.")
        return round(parsed, 2)


class AstroImageExposureTimeAgentService:
    """LLM-backed service for extracting one image's exposure time in hours."""

    def __init__(self, agent: AstroImageExposureTimeAgent) -> None:
        self.agent: AstroImageExposureTimeAgent = agent

    @classmethod
    def create_default(cls) -> AstroImageExposureTimeAgentService:
        """Build the default agent-backed extraction service."""
        provider_name: str = settings.LANDING_PAGE_TOTAL_TIME_SPENT_LLM_PROVIDER
        provider: LLMProvider = LLMProviderRegistry.get(provider_name)
        if isinstance(provider, MockLLMProvider):
            provider.configure(mock_response="0.00")
        return cls(agent=AstroImageExposureTimeAgent(provider=provider))

    def extract_total_hours(self, normalized_exposure_details: str) -> str | None:
        """Delegate exposure-hours extraction to the configured agent."""
        return self.agent.extract_total_hours(normalized_exposure_details)
