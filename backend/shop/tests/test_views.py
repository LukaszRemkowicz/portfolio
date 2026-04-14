import uuid
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.core.cache import cache
from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import _png_field
from core.tests.factories import LandingPageSettingsFactory
from shop.models import ShopSettings
from shop.tests.factories import InactiveShopProductFactory, ShopProductFactory

SHOP_PRODUCT_LIST_URL = "shop:shop-product-list"
SHOP_PRODUCT_DETAIL_URL = "shop:shop-product-detail"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
class TestShopProductListView:
    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture(autouse=True)
    def enable_shop(self) -> None:
        LandingPageSettingsFactory(shop_enabled=True)

    def test_list_returns_only_active_products(self, api_client: APIClient) -> None:
        active = ShopProductFactory(is_active=True)
        ShopProductFactory(is_active=True)
        InactiveShopProductFactory()

        response = api_client.get(reverse(SHOP_PRODUCT_LIST_URL))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["products"]) == 2
        assert any(str(item["id"]) == str(active.pk) for item in response.data["products"])

    def test_list_response_shape(self, api_client: APIClient) -> None:
        ShopProductFactory()

        response = api_client.get(reverse(SHOP_PRODUCT_LIST_URL))
        item = response.data["products"][0]
        assert "title" in response.data
        assert "description" in response.data
        assert "thumbnail_url" in item
        assert "external_url" in item
        assert "created_at" in item

    def test_list_includes_shop_settings_copy(self, api_client: APIClient) -> None:
        ShopProductFactory()
        shop_settings = ShopSettings.objects.create(
            image=_png_field("shop-background.png", size=(1920, 1080))
        )
        shop_settings.set_current_language("en")
        shop_settings.title = "Collect the night sky in print."
        shop_settings.description = "<p>Discover selected astrophotography images.</p>"
        shop_settings.save()

        response = api_client.get(reverse(SHOP_PRODUCT_LIST_URL), {"lang": "en"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Collect the night sky in print."
        assert response.data["description"] == "<p>Discover selected astrophotography images.</p>"

    def test_list_response_is_cached(self, api_client: APIClient) -> None:
        ShopProductFactory()
        list_url = reverse(SHOP_PRODUCT_LIST_URL)

        first_response = api_client.get(list_url)

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            second_response = api_client.get(list_url)

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.json() == first_response.data
        assert any("Cache HIT" in call.args[0] for call in mock_logger.call_args_list)

    def test_list_cache_is_invalidated_on_product_create(self, api_client: APIClient) -> None:
        ShopProductFactory()
        list_url = reverse(SHOP_PRODUCT_LIST_URL)

        api_client.get(list_url)
        new_product = ShopProductFactory()

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert any(str(item["id"]) == str(new_product.pk) for item in response.data["products"])
        assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_list_cache_is_invalidated_on_product_update(self, api_client: APIClient) -> None:
        product = ShopProductFactory()
        list_url = reverse(SHOP_PRODUCT_LIST_URL)

        api_client.get(list_url)
        product.external_url = "https://example.com/updated-product"
        product.save()

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        product_payload = next(
            item for item in response.data["products"] if str(item["id"]) == str(product.pk)
        )
        assert product_payload["external_url"] == "https://example.com/updated-product"
        assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_list_cache_is_invalidated_on_product_delete(self, api_client: APIClient) -> None:
        product = ShopProductFactory()
        list_url = reverse(SHOP_PRODUCT_LIST_URL)

        api_client.get(list_url)
        product_id = str(product.pk)
        product.delete()

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert all(str(item["id"]) != product_id for item in response.data["products"])
        assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_list_cache_is_invalidated_on_shop_settings_update(self, api_client: APIClient) -> None:
        ShopProductFactory()
        shop_settings = ShopSettings.objects.create(
            image=_png_field("shop-background.png", size=(1920, 1080))
        )
        shop_settings.set_current_language("en")
        shop_settings.title = "Collect the night sky in print."
        shop_settings.description = "<p>Original shop copy.</p>"
        shop_settings.save()
        list_url = reverse(SHOP_PRODUCT_LIST_URL)

        api_client.get(list_url, {"lang": "en"})

        shop_settings.set_current_language("en")
        shop_settings.title = "Updated shop title"
        shop_settings.description = "<p>Updated shop copy.</p>"
        shop_settings.save()

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(list_url, {"lang": "en"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated shop title"
        assert response.data["description"] == "<p>Updated shop copy.</p>"
        assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_list_returns_404_when_shop_is_disabled(self, api_client: APIClient) -> None:
        settings_obj = LandingPageSettingsFactory._meta.model.get_current()
        settings_obj.shop_enabled = False
        settings_obj.save()

        response = api_client.get(reverse(SHOP_PRODUCT_LIST_URL))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Shop is currently not available."

    def test_list_rejects_post(self, api_client: APIClient) -> None:
        response = api_client.post(reverse(SHOP_PRODUCT_LIST_URL), data={})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestShopProductDetailView:
    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture(autouse=True)
    def enable_shop(self) -> None:
        LandingPageSettingsFactory(shop_enabled=True)

    def test_detail_returns_200(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)

        response = api_client.get(reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk}))

        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["id"]) == str(product.pk)

    def test_detail_returns_404_for_unknown_id(self, api_client: APIClient) -> None:
        response = api_client.get(reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": uuid.uuid4()}))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_response_is_cached(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)
        detail_url = reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk})

        first_response = api_client.get(detail_url)

        with patch("common.decorators.cache.logger.debug") as mock_logger:
            second_response = api_client.get(detail_url)

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.json() == first_response.data
        assert any("Cache HIT" in call.args[0] for call in mock_logger.call_args_list)

    def test_detail_returns_404_when_shop_is_disabled(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)
        settings_obj = LandingPageSettingsFactory._meta.model.get_current()
        settings_obj.shop_enabled = False
        settings_obj.save()

        response = api_client.get(reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk}))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Shop is currently not available."

    def test_detail_rejects_put(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)

        response = api_client.put(
            reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk}),
            data={},
            format="json",
        )

        product.refresh_from_db()
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert product.is_active is True

    def test_detail_rejects_patch(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)

        response = api_client.patch(
            reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk}),
            data={"external_url": "https://example.com/blocked-update"},
            format="json",
        )

        product.refresh_from_db()
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert product.external_url != "https://example.com/blocked-update"

    def test_detail_rejects_delete(self, api_client: APIClient) -> None:
        product = ShopProductFactory(is_active=True)

        response = api_client.delete(reverse(SHOP_PRODUCT_DETAIL_URL, kwargs={"pk": product.pk}))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert ShopProductFactory._meta.model.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
class TestShopAstroImageLookupView:
    def test_lookup_returns_thumbnail_url_when_available(self, api_client: APIClient) -> None:
        image = AstroImageFactory()
        image.thumbnail = _png_field("lookup-thumb.png", size=(560, 560))
        image.save(update_fields=["thumbnail"])

        response = api_client.get(reverse("shop-image-lookup"), {"id": image.pk})

        assert response.status_code == status.HTTP_200_OK
        assert "lookup-thumb" in response.data["url"]

    def test_lookup_returns_404_for_unknown_id(self, api_client: APIClient) -> None:
        response = api_client.get(reverse("shop-image-lookup"), {"id": uuid.uuid4()})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_lookup_rejects_post(self, api_client: APIClient) -> None:
        response = api_client.post(reverse("shop-image-lookup"), data={})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_lookup_rejects_put(self, api_client: APIClient) -> None:
        response = api_client.put(reverse("shop-image-lookup"), data={}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_lookup_rejects_patch(self, api_client: APIClient) -> None:
        response = api_client.patch(reverse("shop-image-lookup"), data={}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_lookup_rejects_delete(self, api_client: APIClient) -> None:
        response = api_client.delete(reverse("shop-image-lookup"))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
