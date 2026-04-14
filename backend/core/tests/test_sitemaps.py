import pytest

from django.urls import reverse

from core.sitemaps import ShopSitemap, StaticViewSitemap
from core.tests.factories import LandingPageSettingsFactory


@pytest.mark.django_db
class TestStaticViewSitemap:
    def test_static_sitemap_omits_programming_when_disabled(self) -> None:
        LandingPageSettingsFactory(programming_enabled=False)

        sitemap = StaticViewSitemap()

        assert "/programming" not in sitemap.items()

    def test_static_sitemap_includes_programming_when_enabled(self) -> None:
        LandingPageSettingsFactory(programming_enabled=True)

        sitemap = StaticViewSitemap()

        assert "/programming" in sitemap.items()


@pytest.mark.django_db
class TestShopSitemap:
    def test_shop_sitemap_has_no_items_when_shop_is_disabled(self) -> None:
        LandingPageSettingsFactory(shop_enabled=False)

        sitemap = ShopSitemap()

        assert sitemap.items() == []

    def test_shop_sitemap_includes_shop_route_when_shop_is_enabled(self) -> None:
        LandingPageSettingsFactory(shop_enabled=True)

        sitemap = ShopSitemap()

        assert sitemap.items() == ["/shop"]


@pytest.mark.django_db
class TestRootSitemapView:
    def test_root_sitemap_includes_feature_routes_when_enabled(self, client) -> None:
        LandingPageSettingsFactory(shop_enabled=True, programming_enabled=True)

        response = client.get(reverse("sitemap"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "/shop" in content
        assert "/programming" in content

    def test_root_sitemap_omits_feature_routes_when_disabled(self, client) -> None:
        LandingPageSettingsFactory(shop_enabled=False, programming_enabled=False)

        response = client.get(reverse("sitemap"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "/shop" not in content
        assert "/programming" not in content

    def test_root_sitemap_updates_immediately_after_feature_flags_change(self, client) -> None:
        settings_obj = LandingPageSettingsFactory(
            shop_enabled=False,
            programming_enabled=False,
        )

        first_response = client.get(reverse("sitemap"))

        assert first_response.status_code == 200
        first_content = first_response.content.decode("utf-8")
        assert "/shop" not in first_content
        assert "/programming" not in first_content

        settings_obj.shop_enabled = True
        settings_obj.programming_enabled = True
        settings_obj.save(update_fields=["shop_enabled", "programming_enabled"])

        second_response = client.get(reverse("sitemap"))

        assert second_response.status_code == 200
        second_content = second_response.content.decode("utf-8")
        assert "/shop" in second_content
        assert "/programming" in second_content
