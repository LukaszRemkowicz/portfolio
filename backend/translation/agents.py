import logging
from typing import List, Optional

from bs4 import BeautifulSoup

from .protocols import LLMProvider, TranslationAgentProtocol

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "en": "English",
}


class TranslationAgent(TranslationAgentProtocol):
    """
    Agent responsible for translating text and HTML content using LLM providers.
    Supports dual-step translation (Translate then Edit) and HTML structure preservation.

    This agent is provider-agnostic and uses dependency injection to work with any LLM
    (GPT, Gemini, Claude, etc.) that implements the LLMProvider protocol.
    """

    def __init__(self, provider: LLMProvider) -> None:
        """
        Initializes the translation agent with an LLM provider.

        Args:
            provider: LLM provider instance (GPTProvider, GeminiProvider, etc.)
        """
        self.provider = provider

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
        result = self.provider.ask_question(
            system_prompt=prompt,
            user_message=text,
            temperature=0.0,
        )
        if result:
            logger.info(f"Place translation result: '{text}' -> '{result}'")
        else:
            logger.exception(f"LLM place translation failed for '{text}'")
        return result

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
        result = self.provider.ask_question(
            system_prompt=prompt,
            user_message=text,
            temperature=0.0,
        )
        if result:
            logger.info(f"Tag translation result: '{text}' -> '{result}'")
        else:
            logger.exception(f"LLM tag translation failed for '{text}'")
        return result

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
        - CRITICAL: Keep ALL placeholders like [[T0]], [[T1]], [[L0]] etc. EXACTLY as they appear.
        - Do NOT remove, modify, or translate placeholder tokens in double square brackets.
        - Do NOT use metaphors, poetic language, or embellishments.
        - Do NOT use camera or meta narration (no “frame”, “photo”, “widać”, “na zdjęciu”).
        - Use plain, neutral language.
        Return ONLY the translated text with placeholders preserved.
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
        - CRITICAL: Keep ALL placeholders like [[T0]], [[T1]], [[L0]] etc. EXACTLY as they appear.
        - Do NOT remove, modify, or translate placeholder tokens in double square brackets.
        Editing goals:
        - Remove camera/meta narration (e.g. “widać”, “na zdjęciu”).
        - Replace metaphors with plain wording, but keep the original meaning.
        - If an evaluation exists (e.g. “looked exceptional”), keep it in simple, natural form.
        - Keep sentences concise and natural.
        Return ONLY the edited text with all placeholders preserved.
        """.strip()
        lang_name = LANGUAGE_MAP.get(target_lang_code, target_lang_code)

        # ---- CALL 1: TRANSLATE ----
        translated_raw = self.provider.ask_question(
            system_prompt=translation_instructions.format(language=lang_name),
            user_message=text,
            temperature=0.0,
        )

        if not translated_raw:
            logger.warning("LLM returned empty raw translation")
            return None

        logger.info("Raw translation complete, starting editorial refinement")

        # ---- CALL 2: EDIT ----
        final_result = self.provider.ask_question(
            system_prompt=editing_instructions.format(language=lang_name),
            user_message=translated_raw,
            temperature=0.2,
        )

        if final_result:
            logger.info(f"Two-step translation complete for {target_lang_code}")
        else:
            logger.exception("LLM two-step translation failed")

        return final_result

    def _extract_all_html_tags(self, html_content: str) -> tuple[str, dict[int, str]]:
        """
        Extracts ALL HTML tags and replaces them with placeholders [[T0]], [[T1]], etc.
        Returns a tuple of (text_with_placeholders, tag_map).

        Example:
            Input:  "<p><strong>Hello</strong> world</p>"
            Output: ("[[T0]][[T1]]Hello[[T2]] world[[T3]]",
                     {0: "<p>", 1: "<strong>", 2: "</strong>", 3: "</p>"})
        """
        import re

        tag_map = {}
        counter = 0

        # Pattern to match HTML tags (opening, closing, self-closing)
        tag_pattern = re.compile(r"<[^>]+>")

        def replace_tag(match):
            nonlocal counter
            tag = match.group(0)
            placeholder = f"[[T{counter}]]"
            tag_map[counter] = tag
            counter += 1
            return placeholder

        text_with_placeholders = tag_pattern.sub(replace_tag, html_content)
        return text_with_placeholders, tag_map

    def _restore_all_tags(self, translated_text: str, tag_map: dict[int, str]) -> str:
        """
        Restores original HTML tags by replacing placeholders [[T0]], [[T1]], etc.
        with their corresponding tags from the tag_map.
        """
        result = translated_text
        for index, tag in tag_map.items():
            placeholder = f"[[T{index}]]"
            result = result.replace(placeholder, tag)
        return result

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
        Preserves ALL HTML tags and attributes using placeholders to avoid GPT corruption.
        """
        if not text:
            return ""
        logger.info(f"Translating HTML content to {target_lang_code}")

        # Extract all HTML tags and replace with placeholders
        clean_text, tag_map = self._extract_all_html_tags(text)

        # Translate the text with placeholders
        translated = self.translate(clean_text, target_lang_code)
        if translated is None:
            return None

        # Restore original HTML tags
        return self._restore_all_tags(translated, tag_map)
