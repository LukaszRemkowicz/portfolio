from typing import Any

from rest_framework import serializers

from django.conf import settings
from django.urls import reverse

from common.utils.signing import generate_signed_url_params
from translation.services import TranslationService


class SecureMediaURLMixin(serializers.Serializer):
    """
    Mixin to standardize generating signed URLs for secure media fields.
    """

    def get_secure_url(self, resource_id: str, url_name: str) -> str | None:
        if not resource_id:
            return None
        request = self.context.get("request")
        if not request:
            return None
        url_path = reverse(url_name, kwargs={"slug": resource_id})
        params = generate_signed_url_params(
            resource_id, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
        )
        return f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"


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
        self, data: dict[str, Any], instance: Any, fields: list[str]
    ) -> dict[str, Any]:
        """
        Updates the data dictionary with translations for the specified fields.

        When a non-default language is requested, replaces the field value with
        the stored translation (via TranslationService.get_translation which also
        strips any [TRANSLATION FAILED] markers).

        When NO language is requested (default language), we still strip any
        [TRANSLATION FAILED] markers that may have leaked into the field values,
        so they are never exposed to the API / frontend.
        """
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang:
            for field in fields:
                if field in data:
                    val = TranslationService.get_translation(instance, field, lang)
                    if isinstance(val, str) and val.strip() == "<p>&nbsp;</p>":
                        val = ""
                    data[field] = val
        else:
            # Even for the default language, strip any [TRANSLATION FAILED] markers
            # that may have been stored in the DB before the validation fix was deployed.
            # Also strip empty HTML paragraphs from CKEditor.
            prefix = TranslationService.TRANSLATION_FAILED_PREFIX
            for field in fields:
                value = data.get(field)
                if isinstance(value, str):
                    if value.startswith(prefix):
                        data[field] = ""
                    elif value.strip() == "<p>&nbsp;</p>":
                        data[field] = ""

        return data
