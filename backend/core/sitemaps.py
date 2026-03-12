"""
Dynamic sitemap for the portfolio frontend.

Django generates XML using its built-in sitemaps framework.
All location() methods return PATHS only (e.g. /astrophotography/slug).
Django automatically prepends the protocol + host from the incoming request,
so the final <loc> URLs will correctly point to portfolio.local.
"""

from django.contrib.sitemaps import Sitemap

from astrophotography.models import AstroImage, MainPageLocation


class StaticViewSitemap(Sitemap):
    """Hardcoded frontend pages that have no corresponding Django model."""

    changefreq = "daily"
    priority = 1.0
    protocol = "https"

    def items(self) -> list[str]:
        return [
            "/",
            "/astrophotography",
            "/programming",
            "/travel",
            "/privacy",
        ]

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
