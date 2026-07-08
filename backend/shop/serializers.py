from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from common.serializers import TranslatedSerializerMixin

from .models import ShopProduct, ShopSettings


class ShopProductSerializer(
    TranslatedSerializerMixin,
    TranslatableModelSerializer,
):
    """
    Serializer for ShopProduct, exposing translated fields and generated thumbnail variants.

    Serves from the public shop endpoint. Returns translated title and
    description based on the 'lang' query parameter (defaults to English).
    """

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_title(self, instance: ShopProduct) -> str:
        return self.get_translation(instance, "title")

    def get_description(self, instance: ShopProduct) -> str:
        return self.get_translation(instance, "description")

    def to_representation(self, instance: ShopProduct) -> dict:
        data = super().to_representation(instance)
        data.update(instance.get_variant_payload("thumbnail", fallback_width=560))
        return data

    class Meta:
        model = ShopProduct
        fields = [
            "id",
            "title",
            "description",
            "price",
            "currency",
            "external_url",
            "is_active",
            "created_at",
        ]


class ShopSettingsSerializer(
    TranslatedSerializerMixin,
    serializers.ModelSerializer,
):
    """Serializer for the public textual shop settings shown on the storefront."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_title(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "title")

    def get_description(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "description")

    def to_representation(self, instance: ShopSettings) -> dict:
        data = super().to_representation(instance)
        data.update(instance.get_variant_payload("background", fallback_width=2560))
        return data

    class Meta:
        model = ShopSettings
        fields = [
            "title",
            "description",
        ]
