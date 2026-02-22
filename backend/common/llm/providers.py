import logging
from pathlib import Path
from typing import Optional

import openai as openai_module
from openai import OpenAI

from django.conf import settings

from common.exceptions import LLMAuthenticationError
from common.llm.protocols import LLMProvider
from common.llm.registry import LLMProviderRegistry

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Mock provider for testing purposes."""

    def ask_question_with_usage(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> tuple[Optional[str], dict]:
        """Mock LLM response for testing purposes."""
        logger.info("Using mock LLM response for testing purposes.")
        mock_path = Path(settings.BASE_DIR) / "monitoring/tests/llm_mock_response.json"
        with open(mock_path, "r", encoding="utf-8") as f:
            return f.read(), {}

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> Optional[str]:
        """Wrapper for backward compatibility."""
        content, _ = self.ask_question_with_usage(system_prompt, user_message, temperature)
        return content


class GPTProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self) -> None:
        self._openai = openai_module
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
                usage = {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(f"GPT response received (length: {len(result)})")
            return result, usage
        except self._openai.AuthenticationError as e:
            logger.error("GPT Authentication failed (invalid API key)")
            raise LLMAuthenticationError(str(e)) from e
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


# Self-register providers (happens at import time)
LLMProviderRegistry.register("gpt", GPTProvider)
LLMProviderRegistry.register("mock", MockLLMProvider)
