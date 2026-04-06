"""LLM-facing agent for astrophotography exposure-hours extraction."""

from __future__ import annotations

from pathlib import Path

from common.llm.protocols import LLMProvider


class AstroImageExposureTimeAgent:
    """Ask the configured LLM to convert one exposure string into decimal hours."""

    PROMPT_PATH = (
        Path(__file__).parent / "assets" / "prompts" / "astroimage_exposure_time_system.md"
    )

    def __init__(self, provider: LLMProvider) -> None:
        self.provider: LLMProvider = provider

    def extract_total_hours(self, normalized_exposure_details: str) -> str | None:
        """Run the exposure-hours prompt against already-normalized plain text."""
        return self.provider.ask_question(
            system_prompt=self.build_system_prompt(),
            user_message=normalized_exposure_details,
            temperature=0.0,
        )

    @classmethod
    def build_system_prompt(cls) -> str:
        """Load the file-backed system prompt for exposure-hours extraction."""
        return cls.PROMPT_PATH.read_text(encoding="utf-8").strip()
