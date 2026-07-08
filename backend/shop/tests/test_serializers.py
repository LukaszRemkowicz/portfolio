import pytest

from core.tests.factories import ImageVariantFactory
from shop.serializers import ShopProductSerializer
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductSerializer:
    def test_serializer_returns_expected_fields(self) -> None:
        product = ShopProductFactory(
            title="Test Product",
            description="A great product.",
            currency="USD",
            external_url="https://example.com/product",
            is_active=True,
        )

        data = ShopProductSerializer(product).data

        assert set(data) == {
            "id",
            "title",
            "description",
            "fallback_image",
            "variants",
            "price",
            "currency",
            "external_url",
            "is_active",
            "created_at",
        }

    def test_missing_generated_variant_returns_null_fallback(self) -> None:
        product = ShopProductFactory(image=None, thumbnail_url="https://cdn.example.com/thumb.webp")

        data = ShopProductSerializer(product).data

        assert data["fallback_image"] is None
        assert data["variants"] == {"thumbnail": []}

    def test_fallback_image_prefers_generated_thumbnail_variant(self) -> None:
        product = ShopProductFactory(thumbnail_url="https://cdn.example.com/thumb.webp")
        variant = ImageVariantFactory(
            owner=product,
            file__filename="product-crop.webp",
            role="thumbnail",
            width=560,
            height=373,
        )

        data = ShopProductSerializer(product).data

        assert data["fallback_image"] == {
            "url": variant.file.url,
            "width": 560,
            "height": 373,
            "mime_type": "image/webp",
        }
        assert data["variants"] == {"thumbnail": [data["fallback_image"]]}
