from unittest.mock import MagicMock

import pytest

from common.tests.image_helpers import png_field
from shop.serializers import ShopProductSerializer
from shop.tests.factories import ShopProductFactory


class TestShopProductSerializerContract:
    def test_thumbnail_url_uses_product_image_fallback_chain(self) -> None:
        product = MagicMock()
        product.get_image_url.return_value = "/media/shop/product.webp"
        product.thumbnail_url = "https://cdn.example.com/thumb.webp"
        serializer = ShopProductSerializer()

        assert serializer.get_thumbnail_url(product) == "/media/shop/product.webp"
        product.get_image_url.assert_called_once_with("thumbnail", 560)


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
            "thumbnail_url",
            "price",
            "currency",
            "external_url",
            "is_active",
            "created_at",
        }

    def test_thumbnail_url_with_cdn_fallback(self) -> None:
        product = ShopProductFactory(image=None, thumbnail_url="https://cdn.example.com/thumb.webp")

        assert (
            ShopProductSerializer(product).data["thumbnail_url"]
            == "https://cdn.example.com/thumb.webp"
        )

    def test_thumbnail_url_prefers_local_product_variant(self) -> None:
        product = ShopProductFactory(thumbnail_url="https://cdn.example.com/thumb.webp")
        product.image_cropped = png_field("product-crop.png", size=(560, 560))
        product.save()

        assert "product-crop" in ShopProductSerializer(product).data["thumbnail_url"]

    def test_serializer_builds_absolute_media_url(self) -> None:
        request = MagicMock()
        request.build_absolute_uri.side_effect = lambda url: f"https://admin.example.com{url}"

        product = ShopProductFactory()
        product.image_cropped = png_field("absolute-crop.png", size=(560, 560))
        product.save()

        serializer = ShopProductSerializer(product, context={"request": request})

        assert serializer.data["thumbnail_url"].startswith("https://admin.example.com/")
