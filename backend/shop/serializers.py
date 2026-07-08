from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from common.serializers import TranslatedSerializerMixin
from common.types import ImageVariantCandidate

from .models import ShopProduct, ShopSettings


class ShopProductSerializer(
    TranslatedSerializerMixin,
    TranslatableModelSerializer,
):
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
        url = instance.get_image_url(role="thumbnail", width=560) or instance.thumbnail_url
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


class ShopSettingsSerializer(
    TranslatedSerializerMixin,
    serializers.ModelSerializer,
):
    """Serializer for the public textual shop settings shown on the storefront."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    fallback_image = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    def get_title(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "title")

    def get_description(self, instance: ShopSettings) -> str:
        return self.get_translation(instance, "description")

    def get_fallback_image(self, instance: ShopSettings) -> ImageVariantCandidate | None:
        fallback_image = instance.get_variant_candidates("background", preferred_width=2560)
        return fallback_image[0] if fallback_image else None

    def get_variants(self, instance: ShopSettings) -> dict[str, list[ImageVariantCandidate]]:
        return {"background": instance.get_variant_candidates("background")}

    class Meta:
        model = ShopSettings
        fields = [
            "title",
            "description",
            "fallback_image",
            "variants",
        ]
