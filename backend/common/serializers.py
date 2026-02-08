from typing import Any, Dict, List

from rest_framework import serializers

from django.conf import settings

from translation.services import TranslationService


class TranslatedSerializerMixin(serializers.Serializer):
    """
    Mixin to standardize translation retrieval in serializers.
    Avoids repetitive language code checks and TranslationService calls.
    """

    def get_translation(self, instance: Any, field_name: str) -> str:
        """
        Helper to retrieve a translation for a specific field.
        Uses the 'lang' query parameter from the request context.
        """
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if not lang or lang == settings.PARLER_DEFAULT_LANGUAGE_CODE:
            # Return original value if no lang specified, or it's default
            return str(getattr(instance, field_name, ""))

        return TranslationService.get_translation(instance, field_name, lang)

    def translate_fields(
        self, data: Dict[str, Any], instance: Any, fields: List[str]
    ) -> Dict[str, Any]:
        """
        Updates the data dictionary with translations for the specified fields
        if a non-default language is requested.
        """
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != settings.PARLER_DEFAULT_LANGUAGE_CODE:
            for field in fields:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)

        return data
