"""Service helpers for landing-page derived statistics."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from django.conf import settings

from common.llm.protocols import LLMProvider
from common.llm.providers import MockLLMProvider
from common.llm.registry import LLMProviderRegistry

logger = logging.getLogger(__name__)


class LandingPageTotalTimeSpentService:
    """Parse one AstroImage exposure-details string into decimal hours."""

    PROMPT_PATH = (
        Path(__file__).resolve().parent
        / "agent_assets"
        / "prompts"
        / "landing_page_total_time_spent_system.md"
    )

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    @classmethod
    def create_default(cls) -> LandingPageTotalTimeSpentService:
        """Build the service with the configured default LLM provider."""
        provider_name = settings.LANDING_PAGE_TOTAL_TIME_SPENT_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        if isinstance(provider, MockLLMProvider):
            provider.configure(mock_response="0.00")
        return cls(provider=provider)

    def parse_total_hours(self, exposure_details: str) -> float:
        """Normalize exposure text, ask the LLM for hours, and validate the response."""
        normalized_value = self.normalize_exposure_details(exposure_details)
        if not normalized_value:
            return 0.0

        response_text = self.provider.ask_question(
            system_prompt=self._build_system_prompt(),
            user_message=normalized_value,
            temperature=0.0,
        )
        if not response_text:
            raise ValueError("Landing page total time spent response was empty.")

        return self._parse_response_value(response_text)

    @staticmethod
    def normalize_exposure_details(raw_value: str) -> str:
        """Convert HTML-rich exposure text into a compact plain-text string."""
        soup = BeautifulSoup(raw_value, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _build_system_prompt() -> str:
        """Load the system prompt used for the exposure-hours extraction request."""
        return LandingPageTotalTimeSpentService.PROMPT_PATH.read_text(encoding="utf-8").strip()

    @staticmethod
    def _parse_response_value(raw_text: str) -> float:
        """Validate the LLM output as a non-negative float rounded to two decimals."""
        value = raw_text.strip()
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(
                "Landing page total time spent response must be a single number."
            ) from exc
        if parsed < 0:
            raise ValueError("Landing page total time spent response cannot be negative.")
        return round(parsed, 2)
