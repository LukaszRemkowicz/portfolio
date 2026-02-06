# backend/translation/providers.py
import logging
from typing import Optional, Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers (GPT, Gemini, Claude, etc.)."""

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> Optional[str]:
        """
        Ask the LLM a question with system and user prompts.

        Args:
            system_prompt: System-level instructions
            user_message: User's actual content/question
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            LLM's response text, or None on failure
        """
        ...


class GPTProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> Optional[str]:
        """
        Ask GPT a question using OpenAI's chat completions API.

        Args:
            system_prompt: System-level instructions
            user_message: User's actual content/question
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            GPT's response text, or None on failure
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                top_p=1.0,
            )
            result = (response.choices[0].message.content or "").strip()
            logger.debug(f"GPT response received (length: {len(result)})")
            return result
        except Exception:
            logger.exception("GPT API call failed")
            return None
