# backend/shop/tests/test_signals.py
"""
Tests for shop signals.

Validates that cache and SSR invalidation calls are correctly dispatched
when ShopProduct instances and their translations change.
"""

import pytest
from pytest_mock import MockerFixture

from common.tests.image_helpers import _png_field
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductSignals:
    """Signal-level cache invalidation tests."""

    def test_post_save_invalidates_shop_cache(self, mocker: MockerFixture):
        """Cache is cleared every time a ShopProduct is created or updated."""
        mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")
        ShopProductFactory()
        assert mock_cache.call_count >= 1

    def test_post_save_triggers_ssr_cache_invalidation(self, mocker: MockerFixture):
        """SSR cache tag 'shop' is dispatched on every save."""
        mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")
        ShopProductFactory()
        mock_ssr.assert_called_with(["shop"])

    def test_post_delete_invalidates_shop_cache(self, mocker: MockerFixture):
        """Deleting a product clears the backend shop cache."""
        product = ShopProductFactory()

        mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")
        product.delete()

        assert mock_cache.called

    def test_post_delete_triggers_ssr_cache_invalidation(self, mocker: MockerFixture):
        """Deleting a product triggers SSR cache invalidation with 'shop' tag."""
        product = ShopProductFactory()

        mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")
        product.delete()

        mock_ssr.assert_called_with(["shop"])

    def test_update_also_invalidates_cache(self, mocker: MockerFixture):
        """Updating an existing product (not just creation) clears the cache."""
        product = ShopProductFactory()
        mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")

        product.external_url = "https://example.com/updated"
        product.save()

        assert mock_cache.called


@pytest.mark.django_db
class TestShopSettingsSignals:
    """Signal-level cache invalidation tests for storefront settings."""

    def test_post_save_invalidates_shop_cache(self, mocker: MockerFixture):
        mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")

        ShopSettings.objects.create(image=_png_field("shop-background.png"))

        assert mock_cache.called

    def test_post_save_triggers_ssr_cache_invalidation(self, mocker: MockerFixture):
        mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")

        ShopSettings.objects.create(image=_png_field("shop-background.png"))

        mock_ssr.assert_called_with(["shop"])

    def test_update_also_invalidates_cache(self, mocker: MockerFixture):
        settings_obj = ShopSettings.objects.create(image=_png_field("shop-background.png"))
        mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")

        settings_obj.set_current_language("en")
        settings_obj.title = "Updated title"
        settings_obj.save()

        assert mock_cache.called
