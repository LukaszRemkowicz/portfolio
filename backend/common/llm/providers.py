import logging
from pathlib import Path

import openai as openai_module
from openai import OpenAI

from django.conf import settings

from common.exceptions import LLMAuthenticationError
from common.llm.protocols import LLMProvider
from common.llm.registry import LLMProviderRegistry

logger = logging.getLogger(__name__)

# gpt-4o pricing (USD per 1M tokens) — update when OpenAI changes rates
_GPT4O_INPUT_COST_PER_M = 2.50
_GPT4O_OUTPUT_COST_PER_M = 10.00


class MockLLMProvider(LLMProvider):
    """Mock provider for testing purposes."""

    def __init__(self) -> None:
        self._mock_response: str | None = None
        self._mock_usage: dict | None = None
        self._mock_json_path: str | None = None

    def configure(
        self,
        mock_response: str | None = None,
        mock_usage: dict | None = None,
        mock_json_path: str | None = None,
    ) -> None:
        """Configure dynamic mock responses for tests."""
        self._mock_response = mock_response
        self._mock_usage = mock_usage
        self._mock_json_path = mock_json_path

    def ask_question_with_usage(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> tuple[str | None, dict]:
        """Mock LLM response for testing purposes."""
        logger.info("Using mock LLM response for testing purposes.")
        del system_prompt, user_message, temperature

        if self._mock_response is not None:
            return self._mock_response, self._mock_usage or {}

        # Fallback for backward compatibility or custom JSON path
        mock_usage = self._mock_usage or {
            "completion_tokens": 100,
            "prompt_tokens": 500,
            "total_tokens": 600,
            "cost_usd": 0.005,
        }

        if self._mock_json_path:
            mock_path = Path(settings.BASE_DIR) / self._mock_json_path
        else:
            mock_path = Path(settings.BASE_DIR) / "monitoring/tests/llm_responses/default.json"

        with open(mock_path, encoding="utf-8") as f:
            return f.read(), mock_usage

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str | None:
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
    ) -> tuple[str | None, dict]:
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
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                cost_usd = (
                    prompt_tokens / 1_000_000 * _GPT4O_INPUT_COST_PER_M
                    + completion_tokens / 1_000_000 * _GPT4O_OUTPUT_COST_PER_M
                )
                usage = {
                    "completion_tokens": completion_tokens,
                    "prompt_tokens": prompt_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": round(cost_usd, 6),
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
    ) -> str | None:
        """Wrapper for backward compatibility."""
        content, _ = self.ask_question_with_usage(system_prompt, user_message, temperature)
        return content


# Self-register providers (happens at import time)
LLMProviderRegistry.register("gpt", GPTProvider)
LLMProviderRegistry.register("mock", MockLLMProvider)
