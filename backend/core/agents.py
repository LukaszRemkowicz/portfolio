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
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def translate_place(self, text: str, target_lang_code: str, country_name: str) -> Optional[str]:
        if not text:
            return ""
        prompt = f"""
        Translate single words or short phrases from English into {target_lang_code} using the rules below:  # noqa: E501

        1. If the input is a proper noun (e.g. country, city, region, island):
        a) Use the official and commonly accepted {target_lang_code} name if one exists
            (e.g. "Crete" → "Kreta", "Germany" → "Niemcy").
        b) If no established {target_lang_code} equivalent exists, keep the original name unchanged
            (e.g. "Big Hawaii" → "Big Hawaii", "Silicon Valley" → "Silicon Valley").

        2. Do NOT translate proper nouns literally.

        3. If the input is NOT a proper noun, translate it normally into Polish.

        Return only the translation. Do not add explanations or comments.
        If a country ({country_name}) is provided:
        - Use it to disambiguate place names.
        - If the association is uncertain or conflicting, do not translate the name.
        - If user made mistake in place name, correct it (for example, if user wrote "Big Hawai", it should be "Big Hawaii")  # noqa: E501
        """
        try:
            r = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                top_p=1.0,
            )
            return (r.choices[0].message.content or "").strip()
        except Exception:
            logger.exception("GPT translation failed")
            return None

    def translate(self, text: str, target_lang_code: str) -> Optional[str]:
        if not text:
            return ""

        # ===== PROMPT 1: TRANSLATE =====
        TRANSLATE_PROMPT = """
        Translate the text to {language}.
        If we are talking about island which are not translated, return the original name.

        Rules:
        - Preserve meaning exactly.
        - Do not add, remove, or change any information.
        - Keep emojis, punctuation, and line breaks.
        - Do NOT use metaphors, poetic language, or embellishments.
        - Do NOT use camera or meta narration (no “frame”, “photo”, “widać”, “na zdjęciu”).
        - Use plain, neutral language.

        Return ONLY the translated text.
        """.strip()

        # ===== PROMPT 2: EDIT =====
        EDIT_PROMPT = """
        You are editing {language} text into a natural, short photo caption.

        Hard rules:
        - Do NOT change meaning.
        - Do NOT remove evaluations or opinions present in the text.
        - Do NOT add new evaluations.
        - Do NOT change perspective.
        - Keep emojis and punctuation.

        Editing goals:
        - Remove camera/meta narration (e.g. “widać”, “na zdjęciu”).
        - Replace metaphors with plain wording, but keep the original meaning.
        - If an evaluation exists (e.g. “looked exceptional”), keep it in simple, natural form.
        - Keep sentences concise and natural.

        Return ONLY the edited text.
        """.strip()

        try:
            lang_name = LANGUAGE_MAP.get(target_lang_code, target_lang_code)

            # ---- CALL 1: TRANSLATE ----
            r1 = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": TRANSLATE_PROMPT.format(language=lang_name)},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                top_p=1.0,
            )

            translated = (r1.choices[0].message.content or "").strip()
            if not translated:
                return None

            lang_name = LANGUAGE_MAP.get(target_lang_code, target_lang_code)
            # ---- CALL 2: EDIT ----
            r2 = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": EDIT_PROMPT.format(language=lang_name)},
                    {"role": "user", "content": translated},
                ],
                temperature=0.2,
                top_p=1.0,
            )

            return (r2.choices[0].message.content or "").strip()

        except Exception:
            logger.exception("GPT translation failed")
            return None


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()
    # text = "Winter session in the Biała Woda Valley. 🏔️ The frame captures the winter Milky Way along with the Orion constellation and its surrounding nebulosity. On a December night under a blanket of snow, the place looked exceptional. Peace and quiet – nothing more is needed during such trips. Well, except for a clear sky. 😉 ✨"  # noqa: E501
    place = "Big Hawaii"
    agent = GPTTranslationAgent()
    print(agent.translate_place(place, "pl"))
