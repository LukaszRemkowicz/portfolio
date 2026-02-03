"""
Services for managing translations and global state in the core application.
"""
from typing import Any
from django.conf import settings
from parler.models import TranslatableModel

from core.agents import GPTTranslationAgent


class TranslationService:
    @staticmethod
    def get_translated_field(instance: Any, field_name: str, language_code: str) -> str:
        """
        Retrieves the translated value for a given field using Parler.
        If the translation is missing, it triggers an AI Agent to generate it and saves it.
        """
        if not language_code or language_code == "en":
            # Return original/current value (assuming English is default/fallback)
            return getattr(instance, field_name, "")

        # Check if it's a Parler TranslatableModel
        if isinstance(instance, TranslatableModel):
            # 1. Check if translation exists
            if instance.has_translation(language_code):
                # Temporarily switch context to fetch exact translation (avoid fallback logic hiding missing trans)
                # Actually getattr handles it? No, getattr respects current language.
                # safe_translation_getter is better but we want strict check.
                # Since has_translation is True, we can use safe_translation_getter or context switch.
                # Using context switch is robust.
                with instance.language(language_code):
                    return getattr(instance, field_name, "")

            # 2. Translation missing - Generate it
            # Fetch source (English)
            with instance.language("en"):
                source_text = getattr(instance, field_name, "")
            
            if not source_text:
                return ""

            translated_text = GPTTranslationAgent().translate(source_text, language_code)

            if not translated_text:
                translated_text = f"[TRANSLATION FAILED] {source_text}"

            # 3. Save new translation
            # create_translation handles the model creation
            try:
                instance.create_translation(language_code, **{field_name: translated_text})
            except Exception:
                # Race condition or validation error? Fallback to standard save
                pass

            return translated_text

        else:
            # Legacy JSONField logic (fallback)
            original_value = getattr(instance, field_name, "")
            translations = getattr(instance, "translations", {}) or {}
            lang_translations = translations.get(language_code, {})

            if field_name in lang_translations:
                return lang_translations[field_name]

            translated_text = GPTTranslationAgent().translate(original_value, language_code)

            if not translated_text:
                translated_text = f"[TRANSLATION FAILED] {original_value}"

            if language_code not in translations:
                translations[language_code] = {}
            
            translations[language_code][field_name] = translated_text
            instance.translations = translations
            instance.save(update_fields=["translations"])

            return translated_text


    @staticmethod
    def get_available_languages() -> list[str]:
        """
        Returns a list of language codes configured in PARLER_LANGUAGES.
        """
        # Direct extraction from the global 'None' key in PARLER_LANGUAGES
        parler_langs = settings.PARLER_LANGUAGES.get(None, [])
        return [lang['code'] for lang in parler_langs if isinstance(lang, dict) and 'code' in lang]

    def fetch_place_name(self, name: str, country: str, language_code: str) -> str | None:
        return self._gpt_fetch_place_translation(name, country, language_code)

    def _gpt_fetch_place_translation(self, source_text: str, country: str, language_code: str) -> str:
        """Fetches translation from GPT."""
        translated_text = GPTTranslationAgent().translate_place(source_text, language_code, country)

        if not translated_text:
            translated_text = f"[TRANSLATION FAILED] {source_text}"

        return translated_text