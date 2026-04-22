"""
Dynamic sitemap for the portfolio frontend.

Django generates XML using its built-in sitemaps framework.
All location() methods return PATHS only (e.g. /astrophotography/slug).
Django automatically prepends the protocol + host from the incoming request,
so the final <loc> URLs will correctly point to SITE_DOMAIN.
"""

from math import ceil

from django.contrib.sitemaps import Sitemap

from astrophotography.models import AstroImage, MainPageLocation
from astrophotography.pagination import AstroImagePagination
from core.models import LandingPageSettings


class StaticViewSitemap(Sitemap):
    """Hardcoded frontend pages that have no corresponding Django model."""

    changefreq = "daily"
    priority = 1.0
    protocol = "https"

    def items(self) -> list[str]:
        items = [
            "/",
            "/astrophotography",
            "/travel",
            "/privacy",
        ]
        settings_obj = LandingPageSettings.get_current()
        if settings_obj and settings_obj.programming_enabled:
            items.append("/programming")
        return items

    def location(self, item: str) -> str:
        # Return path only — Django prepends scheme + host automatically.
        return item


class AstroImageSitemap(Sitemap):
    """One sitemap entry per astrophotography image (uses slug-based FE URL)."""

    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return AstroImage.objects.all().order_by("-created_at")

    def location(self, obj: AstroImage) -> str:
        return f"/astrophotography/{obj.slug}"

    def lastmod(self, obj: AstroImage):
        return obj.updated_at


class AstroGalleryPaginationSitemap(Sitemap):
    """Paginated public astrophotography gallery URLs such as /astrophotography?page=2."""

    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self) -> list[int]:
        page_size = AstroImagePagination.page_size
        if not page_size:
            return []

        total_images = AstroImage.objects.count()
        total_pages = ceil(total_images / page_size)

        if total_pages <= 1:
            return []

        return list(range(2, total_pages + 1))

    def location(self, page_number: int) -> str:
        return f"/astrophotography?page={page_number}"

    def lastmod(self, _page_number: int):
        latest_image = AstroImage.objects.order_by("-updated_at").first()
        return latest_image.updated_at if latest_image else None


class TravelHighlightsSitemap(Sitemap):
    """One sitemap entry per active MainPageLocation (uses slug-based FE URL)."""

    changefreq = "monthly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return MainPageLocation.objects.filter(is_active=True).order_by("-adventure_date")

    def location(self, obj: MainPageLocation) -> str:
        return f"/travel/{obj.safe_country_slug}/{obj.safe_place_slug}/{obj.date_slug}"

    def lastmod(self, obj: MainPageLocation):
        return obj.updated_at


class ShopSitemap(Sitemap):
    """Expose the public shop route when the shop feature is enabled."""

    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self) -> list[str]:
        settings_obj = LandingPageSettings.get_current()
        if not settings_obj or not settings_obj.shop_enabled:
            return []
        return ["/shop"]

    def location(self, item: str) -> str:
        return item
