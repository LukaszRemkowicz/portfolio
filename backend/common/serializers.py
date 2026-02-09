from typing import Any, Dict, List

from rest_framework import serializers

from translation.services import TranslationService


class TranslatedSerializerMixin(serializers.Serializer):
    """
    Mixin to standardize translation retrieval in serializers.
    Avoids repetitive language code checks and TranslationService calls.
    """

    def get_translation(self, instance: Any, field_name: str) -> str:
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        return TranslationService.get_translation(instance, field_name, str(lang or ""))

    def translate_fields(
        self, data: Dict[str, Any], instance: Any, fields: List[str]
    ) -> Dict[str, Any]:
        """
        Updates the data dictionary with translations for the specified fields
        if a non-default language is requested.
        """
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang:
            for field in fields:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)

        return data
