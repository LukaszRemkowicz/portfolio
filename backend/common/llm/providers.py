import logging
from typing import Optional

from django.conf import settings

from .protocols import LLMProvider

logger = logging.getLogger(__name__)


class GPTProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def ask_question_with_usage(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> tuple[Optional[str], dict]:
        """
        Ask GPT a question and return response + usage stats.
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
            # Handle usage object safely
            usage = {}
            if response.usage:
                # model_dump is standard pydantic v2, fallback to dict if needed
                if hasattr(response.usage, "model_dump"):
                    usage = response.usage.model_dump()
                elif hasattr(response.usage, "to_dict"):
                    usage = response.usage.to_dict()
                else:
                    usage = dict(response.usage)

            logger.debug(f"GPT response received (length: {len(result)})")
            return result, usage
        except Exception:
            logger.exception("GPT API call failed")
            return None, {}

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> Optional[str]:
        """Wrapper for backward compatibility."""
        content, _ = self.ask_question_with_usage(system_prompt, user_message, temperature)
        return content
