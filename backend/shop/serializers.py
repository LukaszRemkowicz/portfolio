from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from common.serializers import TranslatedSerializerMixin

from .models import ShopProduct, ShopSettings


class ShopProductSerializer(TranslatedSerializerMixin, TranslatableModelSerializer):
    """
    Serializer for ShopProduct, exposing translated fields and image URLs.

    Serves from the public shop endpoint. Returns translated title and
    description based on the 'lang' query parameter (defaults to English).
    """

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    def get_title(self, instance: ShopProduct) -> str:
        return self.get_translation(instance, "title")

    def get_description(self, instance: ShopProduct) -> str:
        return self.get_translation(instance, "description")

    def get_thumbnail_url(self, instance: ShopProduct) -> str | None:
        """
        Return the absolute thumbnail URL for the product.
        """
        url = instance.get_thumbnail()
        if not url:
            return None

        request = self.context.get("request")
        if request and url.startswith("/"):
            return str(request.build_absolute_uri(url))

        return url

    class Meta:
        model = ShopProduct
        fields = [
            "id",
            "title",
            "description",
            "thumbnail_url",
            "price",
            "currency",
            "external_url",
            "is_active",
            "created_at",
        ]


class ShopSettingsSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for the public textual shop settings shown on the storefront."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    background_url = serializers.SerializerMethodField()

    def get_title(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "title")

    def get_description(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "description")

    def get_background_url(self, instance: ShopSettings) -> str:
        url = instance.get_serving_url()
        request = self.context.get("request")
        if url and request and url.startswith("/"):
            absolute_url = str(request.build_absolute_uri(url))
            separator = "&" if "?" in absolute_url else "?"
            version = str(int(instance.updated_at.timestamp())) if instance.updated_at else ""
            return f"{absolute_url}{separator}v={version}" if version else absolute_url
        return url

    class Meta:
        model = ShopSettings
        fields = [
            "title",
            "description",
            "background_url",
        ]
