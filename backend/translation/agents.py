import logging
from typing import List, Optional

from bs4 import BeautifulSoup
from openai import OpenAI

from django.conf import settings

from .protocols import TranslationAgentProtocol

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "en": "English",
}


class GPTTranslationAgent(TranslationAgentProtocol):
    """
    Agent responsible for translating text and HTML content using OpenAI's GPT models.
    Supports dual-step translation (Translate then Edit) and HTML structure preservation.
    """

    def __init__(self) -> None:
        """Initializes the OpenAI client using settings."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def translate_place(self, text: str, target_lang_code: str, country_name: str) -> Optional[str]:
        """
        Translates a place name with country context.
        Uses specific rules for proper nouns and disambiguation.
        """
        if not text:
            return ""
        logger.info(f"Translating place '{text}' to {target_lang_code} (Country: {country_name})")
        prompt = f"""
        Translate single words or short phrases from English into {target_lang_code} using the rules below:  # noqa: E501

        1. If the input is a proper noun (e.g. country, city, region, island):
        a) Use the official and commonly accepted {target_lang_code} name if one exists
            (e.g. "Crete" → "Kreta", "Germany" → "Niemcy").
        b) If no established {target_lang_code} equivalent exists, keep the original name unchanged
            (e.g. "Big Hawaii" → "Big Hawaii", "Silicon Valley" → "Silicon Valley").

        2. Do NOT translate proper nouns literally.

        3. If the input is NOT a proper noun, translate it normally into {target_lang_code}.

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
            result = (r.choices[0].message.content or "").strip()
            logger.info(f"Place translation result: '{text}' -> '{result}'")
            return result
        except Exception:
            logger.exception(f"GPT place translation failed for '{text}'")
            return None

    def translate_tag(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates a technical or descriptive tag into the target language.
        Optimized for brevity and technical accuracy (e.g. astronomy or programming).
        """
        if not text:
            return ""
        logger.info(f"Translating tag '{text}' to {target_lang_code}")
        prompt = f"""
        Translate the following tag from English into {target_lang_code}.
        Rules:
        - Keep it brief (usually 1-3 words).
        - Preserve technical accuracy (e.g. for astronomy or programming).
        - Use the most common technical term in {target_lang_code}.
        - Maintain the same capitalization style as the source if possible.
        - Return ONLY the translated tag. No explanations.
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
            result = (r.choices[0].message.content or "").strip()
            logger.info(f"Tag translation result: '{text}' -> '{result}'")
            return result
        except Exception:
            logger.exception(f"GPT tag translation failed for '{text}'")
            return None

    def translate(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates plain text using a two-step process:
        1. Literal translation with strict rule adherence.
        2. Editorial refinement to ensure natural tone and neutral language.
        """
        if not text:
            return ""
        logger.info(f"Translating text to {target_lang_code}")
        # ===== PROMPT 1: TRANSLATE =====
        translation_instructions = """
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
        If there is anchor <a href></a> text, keep it in the same place.
        """.strip()
        # ===== PROMPT 2: EDIT =====
        editing_instructions = """
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
                    {
                        "role": "system",
                        "content": translation_instructions.format(language=lang_name),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                top_p=1.0,
            )
            translated_raw = (r1.choices[0].message.content or "").strip()
            if not translated_raw:
                logger.warning("GPT returned empty raw translation")
                return None
            logger.info("Raw translation complete, starting editorial refinement")
            # ---- CALL 2: EDIT ----
            r2 = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": editing_instructions.format(language=lang_name)},
                    {"role": "user", "content": translated_raw},
                ],
                temperature=0.2,
                top_p=1.0,
            )
            final_result = (r2.choices[0].message.content or "").strip()
            logger.info(f"Two-step translation complete for {target_lang_code}")
            return final_result
        except Exception:
            logger.exception("GPT two-step translation failed")
            return None

    def _extract_links(self, html_content: str) -> tuple[str, List[str]]:
        """
        Extracts <a> tags from HTML and replaces them with placeholders [[L0]], [[L1]] etc.
        Returns a tuple of (html_with_placeholders, original_link_tags).
        """
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        for i, a_tag in enumerate(soup.find_all("a")):
            placeholder = f"[[L{i}]]"
            links.append(str(a_tag))
            a_tag.replace_with(placeholder)
        return str(soup), links

    def _restore_links(self, translated_text: str, links: List[str]) -> str:
        """Restores original <a> tags into text by replacing placeholders."""
        final_text = translated_text
        for i, original_html in enumerate(links):
            placeholder = f"[[L{i}]]"
            final_text = final_text.replace(placeholder, original_html)
        return final_text

    def translate_html(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Orchestrates translation of HTML content.
        Preserves <a> tags using placeholders to avoid GPT corruption of URLs/attributes.
        """
        if not text:
            return ""
        logger.info(f"Translating HTML content to {target_lang_code}")
        clean_text, saved_links = self._extract_links(text)
        translated = self.translate(clean_text, target_lang_code)
        if translated is None:
            return None
        return self._restore_links(translated, saved_links)


if __name__ == "__main__":
    """TODO: Remove this block before production"""
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")
    django.setup()
    text = "text"
    agent = GPTTranslationAgent()
    print(agent.translate_html(text, "pl"))
