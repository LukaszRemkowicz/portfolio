"""
Services for managing translations and global state in the core application.
"""

import logging
from typing import Any

from parler.models import TranslatableModel

from django.conf import settings

from core.agents import GPTTranslationAgent

logger = logging.getLogger(__name__)


class TranslationService:
    @staticmethod
    def get_translated_field(  # noqa: C901, E501
        instance: Any, field_name: str, language_code: str
    ) -> str:
        """
        Retrieves the translated value for a given field.

        Logic:
        1. If language is DEFAULT LANGUAGE, returns the field value directly.
        2. Otherwise, it uses _translate_parler_fields to generate/retrieve
           translations via django-parler and GPT.

        If translation is missing or empty, it triggers GPT to generate it.
        """
        if not language_code or language_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:
            # Return original/current value (assuming English is default/fallback)
            return getattr(instance, field_name, "")

        # Trigger Parler-based translation
        translated_dict = TranslationService._translate_parler_fields(
            instance, [field_name], language_code
        )
        return translated_dict[field_name]

    @staticmethod
    def _translate_parler_fields(
        instance: TranslatableModel, field_names: list[str], language_code: str
    ) -> dict[str, str]:
        """
        Private helper to translate multiple Parler fields at once.

        It checks for existing translations using safe_translation_getter.
        If a field (like 'description' or 'story') contains HTML, it uses
        translate_html to preserve the structure and links.

        Returns a dict of {field_name: translated_text}.
        """
        results = {}
        modified = False
        orig_lang = instance.get_current_language()

        for field_name in field_names:
            # 1. Check if translation exists and contains a value
            current_val = instance.safe_translation_getter(field_name, language_code=language_code)
            if current_val and not TranslationService.is_empty_text(current_val):
                results[field_name] = current_val
                continue

            # 2. Translation missing or empty - Generate it
            # Fetch source (English)
            source_text = instance.safe_translation_getter(
                field_name, language_code=settings.PARLER_DEFAULT_LANGUAGE_CODE
            )

            if not source_text or TranslationService.is_empty_text(source_text):
                results[field_name] = ""
                continue

            if field_name == "description" or field_name == "story":
                logger.info(
                    f"Generating HTML translation for {instance}.{field_name} in {language_code}"
                )
                translated_text = GPTTranslationAgent().translate_html(source_text, language_code)
            else:
                logger.info(
                    f"Generating text translation for {instance}.{field_name} in {language_code}"
                )
                translated_text = GPTTranslationAgent().translate(source_text, language_code)

            if not translated_text:
                logger.warning(f"Translation failed for {instance}.{field_name} in {language_code}")
                translated_text = f"[TRANSLATION FAILED] {source_text}"

            # 3. Mark for update
            instance.set_current_language(language_code)
            setattr(instance, field_name, translated_text)
            results[field_name] = translated_text
            modified = True

        if modified:
            try:
                # Save all translations for the current language
                logger.info(f"Saving translations for {instance} in {language_code}")
                instance.save_translations()
            except Exception as e:
                logger.exception(
                    f"Failed to save translations for {instance} in {language_code}: {e}"
                )
                pass

        # Restore original language context
        instance.set_current_language(orig_lang)
        return results

    @staticmethod
    def is_empty_text(text: Any) -> bool:
        """
        Checks if a string (potentially HTML) is effectively empty.
        Strips HTML tags and &nbsp; entities before checking length.
        """
        if not text:
            return True
        if isinstance(text, str):
            import re

            # Remove HTML tags
            clean = re.sub(r"<[^>]+>", "", text)
            # Remove common HTML entities and whitespace
            clean = clean.replace("&nbsp;", "").strip()
            return not clean
        return False

    @staticmethod
    def translate_main_page_location(instance: Any, language_code: str) -> dict[str, str]:
        """Specific translator for MainPageLocation (highlight_name, story)."""
        fields = ["highlight_name", "story"]
        return TranslationService._translate_parler_fields(instance, fields, language_code)

    @staticmethod
    def translate_astro_image(instance: Any, language_code: str) -> dict[str, str]:
        """Specific translator for AstroImage (name, description, technical details)."""
        fields = ["name", "description", "exposure_details", "processing_details"]
        return TranslationService._translate_parler_fields(instance, fields, language_code)

    @staticmethod
    def get_available_languages() -> list[str]:
        """
        Returns a list of language codes configured in settings.PARLER_LANGUAGES.
        """
        # Direct extraction from the global 'None' key in PARLER_LANGUAGES
        parler_langs = settings.PARLER_LANGUAGES.get(None, [])
        return [lang["code"] for lang in parler_langs if isinstance(lang, dict) and "code" in lang]

    @staticmethod
    def fetch_place_name(name: str, country: str, language_code: str) -> str | None:
        """Public interface to fetch place translation."""
        return TranslationService._gpt_fetch_place_translation(name, country, language_code)

    @staticmethod
    def _gpt_fetch_place_translation(source_text: str, country: str, language_code: str) -> str:
        """Fetches translation for a place name using GPT with country context."""
        translated_text = GPTTranslationAgent().translate_place(source_text, language_code, country)

        if not translated_text:
            translated_text = f"[TRANSLATION FAILED] {source_text}"

        return translated_text
