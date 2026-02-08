"""
Services for managing translations and global state in the core application.
"""

import logging
from typing import TYPE_CHECKING, Any, cast

from parler.models import TranslatableModel

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from .protocols import TranslationAgentProtocol

if TYPE_CHECKING:
    from .agents import TranslationAgent

logger = logging.getLogger(__name__)


class TranslationService:
    agent: TranslationAgentProtocol | None = None

    @classmethod
    def _get_agent(cls) -> "TranslationAgent":
        """
        Lazy-load translation agent with configured LLM provider.

        Returns:
            TranslationAgent: Configured translation agent instance
        """
        if cls.agent is None:
            from .agents import TranslationAgent
            from .factory import get_llm_provider

            provider = get_llm_provider()
            cls.agent = TranslationAgent(provider)

        # Cast strict type for IDE/Mypy, even though runtime is Protocol
        return cast("TranslationAgent", cls.agent)

    @classmethod
    def get_translation(cls, instance: Any, field_name: str, language_code: str) -> str:
        """Pure getter that retrieves an existing translation from the database."""
        if not language_code or language_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:
            return str(getattr(instance, field_name, ""))

        if not isinstance(instance, TranslatableModel):
            return str(getattr(instance, field_name, ""))

        # Check if a translation record exists for this specific language in the DB.
        # This ensures we only return translations that have been explicitly created.
        if not instance.translations.filter(language_code=language_code).exists():
            return ""

        # Strictly get the translation for the specified language without fallback.
        return str(
            instance.safe_translation_getter(
                field_name, language_code=language_code, any_language=False
            )
            or ""
        )

    @classmethod
    def _has_translation(
        cls, instance: TranslatableModel, field_name: str, language_code: str, force: bool = False
    ) -> tuple[bool, Any]:
        """
        Checks if a translation exists in the database for the given field and language.
        Returns (True, value) if it exists, (False, None) otherwise.
        If force is True, always returns (False, None) to trigger re-translation.
        """
        if force:
            logger.info(f"Force translation enabled for '{field_name}' in '{language_code}'.")
            return False, None

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
    def _parler_ceremony(
        cls, instance: TranslatableModel, field_name: str, language_code: str, force: bool = False
    ):
        """
        Generator to handle Parler translation infrastructure (checks, source, save).
        1. Checks for existing translation.
        2. Yields source text to caller.
        3. Receives translated text via .send().
        4. Updates instance and handles language context.
        """
        # 1. Check existence
        has_translation, current_val = cls._has_translation(
            instance, field_name, language_code, force=force
        )
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
        cls,
        instance: TranslatableModel,
        field_name: str,
        language_code: str,
        handler: Any,
        force: bool = False,
    ) -> str:
        """
        Helper that runs the ceremony for a single field using a provided handler.
        """
        gen = cls._parler_ceremony(instance, field_name, language_code, force=force)
        source = next(gen)

        if source is None:
            # Already exists or source empty
            return str(
                instance.safe_translation_getter(field_name, language_code=language_code) or ""
            )

        # Call the specialized handler
        logger.info(f"Translating field '{field_name}' using {handler.__name__}")
        translated = handler(source, language_code)

        if not translated:
            translated = f"[TRANSLATION FAILED] {source}"

        try:
            gen.send(translated)
        except StopIteration:
            pass

        return str(translated)

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
    def translate_main_page_location(
        cls, instance: Any, language_code: str, force: bool = False
    ) -> dict[str, str]:
        """Specific translator for MainPageLocation (highlight_name, story)."""
        results = {}

        # 'highlight_name' is text, 'story' is HTML
        results["highlight_name"] = cls._run_parler_translation(
            instance, "highlight_name", language_code, cls._get_agent().translate, force=force
        )
        results["story"] = cls._run_parler_translation(
            instance, "story", language_code, cls._get_agent().translate_html, force=force
        )

        try:
            with transaction.atomic():
                instance.save_translations()
        except Exception:
            logger.exception("Failed to save MainPageLocation translations")

        return results

    @classmethod
    def translate_astro_image(
        cls, instance: Any, language_code: str, force: bool = False
    ) -> dict[str, str]:
        """Specific translator for AstroImage (name, description, technical details)."""
        results = {}

        # 'description' is HTML, others are text
        fields = ["name", "description", "exposure_details", "processing_details"]
        for field in fields:
            handler = (
                cls._get_agent().translate_html
                if field == "description"
                else cls._get_agent().translate
            )
            results[field] = cls._run_parler_translation(
                instance, field, language_code, handler, force=force
            )

        try:
            with transaction.atomic():
                instance.save_translations()
        except Exception:
            logger.exception("Failed to save AstroImage translations")

        return results

    @classmethod
    def translate_user(
        cls, instance: Any, language_code: str, force: bool = False
    ) -> dict[str, str]:
        """
        Specific translator for User (short_description, bio).
        Handles different content types:
        - short_description: plain text
        - bio: HTML
        """
        results = {}

        # Define which handler to use for each field
        field_config = {
            "short_description": cls._get_agent().translate,
            "bio": cls._get_agent().translate_html,
        }

        for field, handler in field_config.items():
            results[field] = cls._run_parler_translation(
                instance, field, language_code, handler, force=force
            )

        try:
            with transaction.atomic():
                instance.save_translations()
        except Exception:
            logger.exception(f"Failed to save User translations for {instance}")

        return results

    @classmethod
    def translate_parler_tag(
        cls, instance: Any, language_code: str, force: bool = False
    ) -> list[str]:
        """
        Specialized translator for Tags.
        Translates name from English (if missing or forced) and syncs slug locally.
        """
        orig_lang = instance.get_current_language()
        results = []
        try:
            instance.set_current_language(language_code)

            # 1. Name: Translate from English if missing OR forced
            has_name, _ = cls._has_translation(instance, "name", language_code)
            if not has_name or force:
                source = cls._get_default_language_text(instance, "name")
                if source:
                    logger.info(
                        f"Translating Tag name '{source}' to {language_code} (force={force})"
                    )
                    new_name = cls._get_agent().translate_tag(source, language_code)
                    if new_name:
                        instance.name = new_name
                        results.append(new_name)

            # 2. Slug: Local sync from the translated name
            if instance.name:
                expected_slug = slugify(instance.name, allow_unicode=True)
                has_slug, current_slug = cls._has_translation(instance, "slug", language_code)

                if not has_slug or current_slug != expected_slug:
                    logger.info(
                        f"Sync Tag slug [{language_code}]: '{current_slug}' -> '{expected_slug}'"
                    )
                    instance.slug = expected_slug
                    results.append(expected_slug)

            if results:
                with transaction.atomic():
                    instance.save_translations()
                logger.info(f"Saved Tag translations for {language_code}: {results}")

        except Exception:
            logger.exception(f"Failed to process Tag translations for {language_code}")
        finally:
            instance.set_current_language(orig_lang)

        return results

    @classmethod
    def translate_place(cls, instance: Any, language_code: str, force: bool = False) -> str:
        """
        Specialized translator for Place names.
        Uses specialized place translation logic with country context.
        """
        country_name = str(instance.country) if hasattr(instance, "country") else ""

        # We define a local handler that includes the country context
        def place_handler(text: str, lang: str) -> str:
            return cls._get_agent().translate_place(text, lang, country_name) or ""

        translated = cls._run_parler_translation(
            instance, "name", language_code, place_handler, force=force
        )

        try:
            with transaction.atomic():
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
