import logging
from typing import Optional

from openai import OpenAI

from django.conf import settings

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "en": "English",
}


class GPTTranslationAgent:
    def __init__(self) -> None:
        # Client initializes using OPENAI_API_KEY from env by default
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def translate(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates text to the target language using GPT-4.
        Returns the translated string, or None if the API call fails.
        """
        if not text:
            return ""

        language_name = LANGUAGE_MAP.get(target_lang_code, target_lang_code)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional translator. Translate the following text to {language_name}. "  # noqa: E501
                            "Return ONLY the translated text, preserving original formatting and markdown if present. "  # noqa: E501
                            "Do not add any explanations or quotes."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"GPT translation failed for lang={target_lang_code}: {e}")
            return None
