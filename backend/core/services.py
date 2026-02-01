from typing import Any


class TranslationService:
    @staticmethod
    def get_translated_field(instance: Any, field_name: str, language_code: str) -> str:
        """
        Retrieves the translated value for a given field from the instance's
        'translations' JSONField.
        If the translation is missing, it creates a stub translation and saves it to the instance.
        """
        # 1. Start with the default (English) value
        original_value = getattr(instance, field_name, "")
        if not language_code or language_code == "en":
            return original_value

        # 2. Check existing translations
        translations = getattr(instance, "translations", {}) or {}
        lang_translations = translations.get(language_code, {})

        if field_name in lang_translations:
            return lang_translations[field_name]

        # 3. Translation missing - Call AI Agent
        from core.ai_agents import GPTTranslationAgent

        translated_text = GPTTranslationAgent().translate(original_value, language_code)

        if not translated_text:
            # Fallback if Agent fails
            translated_text = f"[TRANSLATION FAILED] {original_value}"

        # 4. Save the new translation to the instance
        if language_code not in translations:
            translations[language_code] = {}

        translations[language_code][field_name] = translated_text
        instance.translations = translations

        # Save only the translations field to avoid race conditions or overwriting other fields
        instance.save(update_fields=["translations"])

        return translated_text
