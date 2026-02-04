"""
Services for managing translations and global state in the core application.
"""

import logging
from typing import Any

from parler.models import TranslatableModel

from django.conf import settings

from core.agents import GPTTranslationAgent
from core.protocols import TranslationAgentProtocol

logger = logging.getLogger(__name__)


class TranslationService:
    agent: TranslationAgentProtocol = GPTTranslationAgent()

    @classmethod
    def get_translation(cls, instance: Any, field_name: str, language_code: str) -> str:
        """Pure getter that retrieves an existing translation from the database."""
        if not language_code or language_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:
            return getattr(instance, field_name, "")

        if not isinstance(instance, TranslatableModel):
            return getattr(instance, field_name, "")

        return (
            instance.safe_translation_getter(
                field_name, language_code=language_code, any_language=False
            )
            or ""
        )

    @classmethod
    def _has_translation(
        cls, instance: TranslatableModel, field_name: str, language_code: str
    ) -> tuple[bool, Any]:
        """
        Checks if a translation exists in the database for the given field and language.
        Returns (True, value) if it exists, (False, None) otherwise.
        """
        has_record = instance.translations.filter(language_code=language_code).exists()
        current_val = instance.safe_translation_getter(
            field_name, language_code=language_code, any_language=False
        )

        logger.info(
            f"Field '{field_name}' in '{language_code}': exists={has_record}, val='{current_val}'"
        )

        if has_record and current_val and not cls.is_empty_text(current_val):
            logger.info(f"Skipping '{field_name}' in '{language_code}' - translation record found.")
            return True, current_val
        return False, None

    @classmethod
    def _get_default_language_text(cls, instance: TranslatableModel, field_name: str) -> str:
        """
        Gets the text from the default language.
        """
        return str(
            instance.safe_translation_getter(
                field_name, language_code=settings.PARLER_DEFAULT_LANGUAGE_CODE
            )
            or ""
        )

    @classmethod
    def _parler_ceremony(cls, instance: TranslatableModel, field_name: str, language_code: str):
        """
        Generator to handle Parler translation infrastructure (checks, source, save).
        1. Checks for existing translation.
        2. Yields source text to caller.
        3. Receives translated text via .send().
        4. Updates instance and handles language context.
        """
        # 1. Check existence
        has_translation, current_val = cls._has_translation(instance, field_name, language_code)
        if has_translation:
            yield None  # Signal that we should skip
            return

        # 2. Get source
        source_text = cls._get_default_language_text(instance, field_name)
        if not source_text or cls.is_empty_text(source_text):
            yield None
            return

        # 3. Hand off to specialized method
        # Caller should call .send(translated_text)
        translated_text = yield source_text

        if not translated_text:
            return

        # 4. Finalize update
        orig_lang = instance.get_current_language()
        try:
            instance.set_current_language(language_code)
            setattr(instance, field_name, translated_text)
            logger.info(f"Set '{field_name}' in '{language_code}' for {instance}")
        finally:
            instance.set_current_language(orig_lang)

    @classmethod
    def _run_parler_translation(
        cls, instance: TranslatableModel, field_name: str, language_code: str, handler: Any
    ) -> str:
        """
        Helper that runs the ceremony for a single field using a provided GPT handler.
        """
        gen = cls._parler_ceremony(instance, field_name, language_code)
        source = next(gen)

        if source is None:
            # Already exists or source empty
            return str(
                instance.safe_translation_getter(field_name, language_code=language_code) or ""
            )

        # Call the specialized GPT handler
        logger.info(f"Translating field '{field_name}' using {handler.__name__}")
        translated = handler(source, language_code)

        if not translated:
            translated = f"[TRANSLATION FAILED] {source}"

        try:
            gen.send(translated)
        except StopIteration:
            pass

        return str(translated)

    @classmethod
    def _bulk_sync_translations(
        cls, instance: TranslatableModel, field_names: list[str], language_code: str
    ) -> dict[str, str]:
        """
        A generic helper for multi-field translation.
        Defaults to standard text translation if not overridden by specialized methods.
        """
        results = {}
        modified = False

        for field_name in field_names:
            # Default to agent.translate
            # Specialized methods (like translate_astro_image) should not call this
            # if they need custom field-level logic (like HTML).
            val = cls._run_parler_translation(
                instance, field_name, language_code, cls.agent.translate
            )
            results[field_name] = val
            modified = True

        if modified:
            try:
                instance.save_translations()
            except Exception as e:
                logger.exception(f"Failed to save translations for {instance}: {e}")

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

    @classmethod
    def translate_main_page_location(cls, instance: Any, language_code: str) -> dict[str, str]:
        """Specific translator for MainPageLocation (highlight_name, story)."""
        results = {}

        # 'highlight_name' is text, 'story' is HTML
        results["highlight_name"] = cls._run_parler_translation(
            instance, "highlight_name", language_code, cls.agent.translate
        )
        results["story"] = cls._run_parler_translation(
            instance, "story", language_code, cls.agent.translate_html
        )

        try:
            instance.save_translations()
        except Exception:
            logger.exception("Failed to save MainPageLocation translations")

        return results

    @classmethod
    def translate_astro_image(cls, instance: Any, language_code: str) -> dict[str, str]:
        """Specific translator for AstroImage (name, description, technical details)."""
        results = {}

        # 'description' is HTML, others are text
        fields = ["name", "description", "exposure_details", "processing_details"]
        for field in fields:
            handler = cls.agent.translate_html if field == "description" else cls.agent.translate
            results[field] = cls._run_parler_translation(instance, field, language_code, handler)

        try:
            instance.save_translations()
        except Exception:
            logger.exception("Failed to save AstroImage translations")

        return results

    @classmethod
    def translate_parler_tag(cls, instance: Any, language_code: str) -> str:
        """
        Specialized translator for Tags.
        Uses specialized GPT tag agent.
        Translates from the shared 'name' field to the localized 'name' field.
        """
        result = cls._run_parler_translation(
            instance,
            "title",
            language_code,
            cls.agent.translate_tag,
        )
        if result:
            instance.save_translations()
        return result

    @classmethod
    def translate_place(cls, instance: Any, language_code: str) -> str:
        """
        Specialized translator for Place names.
        Uses specialized GPT place agent with country context.
        """
        country_name = str(instance.country) if hasattr(instance, "country") else ""

        # We define a local handler that includes the country context
        def place_handler(text: str, lang: str) -> str:
            return cls.agent.translate_place(text, lang, country_name) or ""

        translated = cls._run_parler_translation(instance, "name", language_code, place_handler)

        try:
            instance.save_translations()
        except Exception:
            logger.exception(f"Failed to save Place translations for {instance}")

        return translated

    @staticmethod
    def get_available_languages() -> list[str]:
        """
        Returns a list of language codes configured in settings.PARLER_LANGUAGES.
        """
        # Direct extraction from the global 'None' key in PARLER_LANGUAGES
        parler_langs = settings.PARLER_LANGUAGES.get(None, [])
        return [lang["code"] for lang in parler_langs if isinstance(lang, dict) and "code" in lang]

    @classmethod
    def fetch_place_name(cls, name: str, country: str, language_code: str) -> str | None:
        """Public interface to fetch place translation (without a model instance)."""
        return cls._gpt_fetch_place_translation(name, country, language_code)

    @classmethod
    def _gpt_fetch_place_translation(
        cls, source_text: str, country: str, language_code: str
    ) -> str:
        """Fetches translation for a place name using GPT with country context."""
        translated_text = cls.agent.translate_place(source_text, language_code, country)

        if not translated_text:
            translated_text = f"[TRANSLATION FAILED] {source_text}"

        return translated_text
