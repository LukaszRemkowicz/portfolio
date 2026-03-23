"""
Services for managing translations and global state in the core application.
"""

import functools
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

from parler.models import TranslatableModel

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from common.llm.protocols import TranslationAgentProtocol
from common.llm.registry import LLMProviderRegistry

from .agents import TranslationAgent

logger = logging.getLogger(__name__)


@dataclass
class FieldTranslationConfig:
    """Configuration for translating a single field."""

    name: str
    is_html: bool = False
    custom_handler: Optional[Callable[[str, str], str]] = None


class TranslationService:
    """Service for translating model instances."""

    # Configuration for model-specific field translations
    TRANSLATION_CONFIGS: dict[str, list[FieldTranslationConfig]] = {
        "AstroImage": [
            FieldTranslationConfig("name"),
            FieldTranslationConfig("description", is_html=True),
            FieldTranslationConfig("exposure_details"),
            FieldTranslationConfig("processing_details"),
        ],
        "User": [
            FieldTranslationConfig("short_description"),
            FieldTranslationConfig("bio", is_html=True),
        ],
        "Profile": [
            FieldTranslationConfig("title"),
            FieldTranslationConfig("specific_bio", is_html=True),
        ],
        "MainPageBackgroundImage": [
            FieldTranslationConfig("name"),
            FieldTranslationConfig("description", is_html=True),
        ],
        "ProjectImage": [
            FieldTranslationConfig("name"),
            FieldTranslationConfig("description", is_html=True),
        ],
        "MainPageLocation": [
            FieldTranslationConfig("highlight_name"),
            FieldTranslationConfig("highlight_title"),
            FieldTranslationConfig("story", is_html=True),
        ],
    }

    def __init__(self, agent: TranslationAgentProtocol):
        """
        Initialize translation service with agent.

        Args:
            agent: Translation agent instance
        """
        self.agent = agent

    @classmethod
    def create_default(cls) -> "TranslationService":
        """
        Factory method to create service with default dependencies.

        Returns:
            TranslationService: Configured translation service instance
        """
        # Fail-fast: No defaults, settings must be explicit
        provider_name = settings.TRANSLATION_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        agent = TranslationAgent(provider)
        return cls(agent)

    def _get_handler(self, field_config: FieldTranslationConfig) -> Callable[[str, str], str]:
        """
        Get the appropriate translation handler for a field configuration.
        Binds field_hint so the LLM knows which field it is translating,
        preventing it from treating short/technical strings as input mistakes.
        """
        if field_config.custom_handler:
            return field_config.custom_handler
        base = self.agent.translate_html if field_config.is_html else self.agent.translate
        return functools.partial(base, field_hint=field_config.name)  # type: ignore[return-value]

    def _save_translations(self, instance: TranslatableModel, model_name: str) -> None:
        """
        Save translations for an instance with error handling.

        Args:
            instance: Model instance to save
            model_name: Name of the model (for logging)
        """
        try:
            with transaction.atomic():
                instance.save_translations()
        except Exception:
            logger.exception(f"Failed to save {model_name} translations")

    def translate_model(
        self,
        instance: TranslatableModel,
        language_code: str,
        force: bool = False,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """
        Generic translation method for any configured model.

        This method eliminates code duplication by using configuration-based
        field handling. Models are configured in TRANSLATION_CONFIGS.

        Args:
            instance: TranslatableModel instance to translate
            language_code: Target language code
            force: Force re-translation even if translation exists

        Returns:
            Dictionary mapping field names to translated values

        Raises:
            ValueError: If model is not configured in TRANSLATION_CONFIGS
        """
        model_name = instance.__class__.__name__
        config = self.TRANSLATION_CONFIGS.get(model_name)

        if not config:
            raise ValueError(
                f"No translation config for {model_name}. "
                f"Add configuration to TranslationService.TRANSLATION_CONFIGS"
            )

        results = {}
        failures = {}  # Map: {field_name: failure_reason}
        for field_config in config:
            # Bind field_hint so the LLM knows what it is translating
            handler = functools.partial(  # type: ignore[call-arg]
                self._get_handler(field_config), field_hint=field_config.name
            )
            translated, reason = self._run_parler_translation(
                instance, field_config.name, language_code, handler, force=force
            )
            results[field_config.name] = translated
            if reason:
                failures[field_config.name] = reason

        self._save_translations(instance, model_name)
        return results, failures

    TRANSLATION_FAILED_PREFIX: str = "[TRANSLATION FAILED]"

    @staticmethod
    def get_translation(instance: Any, field_name: str, language_code: str) -> str:
        """
        Pure getter that retrieves an existing translation from the database.

        If the stored value is a failure marker or does not exist, transparently
        falls back to the default application language (English) so the API always
        has content to display.
        """
        default_language = settings.DEFAULT_APP_LANGUAGE
        requested_language = language_code or default_language

        if not isinstance(instance, TranslatableModel):
            return str(getattr(instance, field_name, ""))

        def read_translation(lang: str) -> str:
            if not instance.translations.filter(language_code=lang).exists():
                return ""

            value = str(
                instance.safe_translation_getter(field_name, language_code=lang, any_language=False)
                or ""
            )

            if value.startswith(TranslationService.TRANSLATION_FAILED_PREFIX):
                return ""

            if value.strip() == "<p>&nbsp;</p>":
                return ""

            return value

        value = read_translation(requested_language)
        if value:
            return value

        if requested_language != default_language:
            return read_translation(default_language)

        return ""

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
                field_name, language_code=settings.DEFAULT_APP_LANGUAGE
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

    # Known LLM refusal prefixes (case-insensitive check)
    REFUSAL_PREFIXES: tuple[str, ...] = (
        "i'm sorry",
        "i am sorry",
        "i cannot",
        "i can't",
        "could you please",
        "it seems like",
        "there might be a mistake",
        "please provide",
        "i apologize",
        "as an ai",
    )

    @staticmethod
    def _is_valid_translation(source: str, translated: str) -> bool:
        """
        Returns False when the LLM response is a refusal or clearly not a translation.

        Rejects output that:
        - Starts with a known refusal phrase (LLM politely refusing the request)
        - Is byte-for-byte identical to the source (no translation happened)
        """
        if not translated:
            return False
        lower = translated.strip().lower()
        for prefix in TranslationService.REFUSAL_PREFIXES:
            if lower.startswith(prefix):
                logger.warning(
                    f"[TRANSLATION REFUSED] LLM returned a refusal message. "
                    f"Source (truncated): '{source[:60]}...'"
                )
                return False
        if translated.strip() == source.strip():
            logger.warning(
                f"[TRANSLATION NOOP] LLM returned identical text to source for: '{source[:60]}...'"
            )
            return False
        return True

    @classmethod
    def _run_parler_translation(
        cls,
        instance: TranslatableModel,
        field_name: str,
        language_code: str,
        handler: Any,
        force: bool = False,
    ) -> tuple[str, Optional[str]]:
        """
        Helper that runs the ceremony for a single field using a provided handler.
        Returns (translated_text, failure_reason_or_None).
        """
        gen = cls._parler_ceremony(instance, field_name, language_code, force=force)
        source = next(gen)

        if source is None:
            # Already exists or source empty
            val = str(
                instance.safe_translation_getter(field_name, language_code=language_code) or ""
            )
            return val, None

        # Call the specialized handler
        handler_name = getattr(handler, "__name__", None) or getattr(
            getattr(handler, "func", None), "__name__", repr(handler)
        )
        logger.info(f"Translating field '{field_name}' using {handler_name}")

        translated = handler(source, language_code)

        reason = None
        if not translated:
            reason = "Empty Output"
        elif translated.strip() == source.strip():
            # Identity match: the LLM returned the same text as the source.
            # This is valid for proper nouns that don't change across languages
            # (e.g. "Lanzarote", "Maui", "Tenerife"). Accept the source value
            # as the correct translation so the task is marked successful.
            translated = source
            logger.info(
                f"[IDENTITY MATCH] field='{field_name}' lang='{language_code}' "
                f"source='{source[:80]}' — accepted as-is (proper noun / unchanged)."
            )
        else:
            # Check for LLM Refusal messages
            lower = translated.strip().lower()
            for prefix in cls.REFUSAL_PREFIXES:
                if lower.startswith(prefix):
                    reason = f"LLM Refusal: {str(translated).strip()[:200]}"
                    break

        if reason:
            logger.warning(
                f"[TRANSLATION FAILED] field='{field_name}' lang='{language_code}' "
                f"reason='{reason}' source='{source[:80]}'"
            )
            translated = ""

        try:
            gen.send(translated)
        except StopIteration:
            pass

        return str(translated), reason

    @staticmethod
    def is_empty_text(text: Any) -> bool:
        """
        Checks if a string (potentially HTML) is effectively empty.
        Strips HTML tags and &nbsp; entities before checking length.
        """
        if not text:
            return True
        if isinstance(text, str):
            # Remove HTML tags
            clean = re.sub(r"<[^>]+>", "", text)
            # Remove common HTML entities and whitespace
            clean = clean.replace("&nbsp;", "").strip()
            return not clean
        return False

    def translate_main_page_location(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate MainPageLocation (highlight_name, highlight_title, story)."""
        return self.translate_model(instance, language_code, force)

    def translate_astro_image(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate AstroImage (name, description, exposure_details, processing_details)."""
        return self.translate_model(instance, language_code, force)

    def translate_user(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate User (short_description, bio)."""
        return self.translate_model(instance, language_code, force)

    def translate_profile(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate Profile (title, specific_bio)."""
        return self.translate_model(instance, language_code, force)

    def translate_main_page_background_image(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate MainPageBackgroundImage (name, description)."""
        return self.translate_model(instance, language_code, force)

    def translate_project_image(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Translate ProjectImage (name, description)."""
        return self.translate_model(instance, language_code, force)

    def translate_parler_tag(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[list[str], dict[str, str]]:
        """
        Specialized translator for Tags.
        Translates name from English (if missing or forced) and syncs slug locally.
        """
        orig_lang = instance.get_current_language()
        results = []
        failures = {}
        try:
            instance.set_current_language(language_code)

            # 1. Name: Translate from English if missing OR forced
            has_name, _ = self._has_translation(instance, "name", language_code)
            if not has_name or force:
                source = self._get_default_language_text(instance, "name")
                if source:
                    logger.info(
                        f"Translating Tag name '{source}' to {language_code} (force={force})"
                    )
                    # Use specialized tag translator
                    new_name = self.agent.translate_tag(source, language_code)
                    if new_name:
                        # Validate the result (tags are usually short, so no complex validation)
                        instance.name = new_name
                        results.append(new_name)
                    else:
                        failures["name"] = "LLM Failed"

            # 2. Slug: Local sync from the translated name
            if instance.name:
                expected_slug = slugify(instance.name, allow_unicode=True)
                has_slug, current_slug = self._has_translation(instance, "slug", language_code)

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

        except Exception as exc:
            logger.exception(f"Failed to process Tag translations for {language_code}")
            failures["__all__"] = str(exc)
        finally:
            instance.set_current_language(orig_lang)

        return results, failures

    def translate_place(
        self, instance: Any, language_code: str, force: bool = False
    ) -> tuple[str, dict[str, str]]:
        """
        Specialized translator for Place names.
        Uses specialized place translation logic with country context.
        """
        country_name = str(instance.country) if hasattr(instance, "country") else ""
        failures = {}

        # We define a local handler that includes the country context
        def place_handler(text: str, lang: str, field_hint: str = "") -> str:
            return self.agent.translate_place(text, lang, country_name) or ""

        translated, reason = self._run_parler_translation(
            instance, "name", language_code, place_handler, force=force
        )

        if reason:
            failures["name"] = reason

        try:
            with transaction.atomic():
                instance.save_translations()
        except Exception as exc:
            logger.exception(f"Failed to save Place translations for {instance}")
            failures["__save__"] = str(exc)

        return translated, failures

    @staticmethod
    def get_available_languages() -> list[str]:
        """
        Returns a list of language codes configured in settings.PARLER_LANGUAGES.
        """
        # Direct extraction from the global 'None' key in PARLER_LANGUAGES
        parler_langs = settings.PARLER_LANGUAGES.get(None, [])
        return [lang["code"] for lang in parler_langs if isinstance(lang, dict) and "code" in lang]
