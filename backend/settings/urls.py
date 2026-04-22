"""
URL Configuration for the core application.

This file defines the main routing table for the project, including:
- API v1 endpoints (users, astrophotography, inbox, settings)
- System health checks
- Admin site URLs (when current host matches ADMIN_DOMAIN)
- Third-party integrations (Select2, CKEditor 5)
- Dynamic CSS for Parler-based admin translations
- Media file serving (on admin domain)
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import Http404
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.static import serve

from astrophotography.views import AstroImageSecureView, ImageURLViewSet
from core.sitemaps import (
    AstroGalleryPaginationSitemap,
    AstroImageSitemap,
    ShopSitemap,
    StaticViewSitemap,
    TravelHighlightsSitemap,
)
from core.views import health_check_view, root_view
from shop.views import ShopAstroImageLookupView

from .api_urls import (
    admin_secure_media_urlpatterns,
    api_v1_base_urlpatterns,
    api_v1_catch_all_urlpatterns,
)

admin.site.site_header = "Portfolio Administration"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"

_sitemaps = {
    "static": StaticViewSitemap,
    "astro-pages": AstroGalleryPaginationSitemap,
    "astro": AstroImageSitemap,
    "shop": ShopSitemap,
    "travel": TravelHighlightsSitemap,
}

urlpatterns = [
    path("health", health_check_view, name="health"),
    path(
        "image-files/<slug:slug>/serve/",
        AstroImageSecureView.as_view(),
        name="secure-image-file",
    ),
    path(
        "image-urls/",
        ImageURLViewSet.as_view({"get": "list"}),
        name="image-urls-list",
    ),
    path(
        "image-urls/<slug:pk>/",
        ImageURLViewSet.as_view({"get": "retrieve"}),
        name="image-urls-detail",
    ),
    *api_v1_base_urlpatterns,
    path("select2/", include("django_select2.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path(
        "api/v1/shop/image-lookup/",
        ShopAstroImageLookupView.as_view(),
        name="shop-image-lookup",
    ),
    path("", include("translation.urls")),
    path("admin/", admin.site.urls),
    # Sitemap at root so Google finds it at /sitemap.xml.
    # Cache for 12 hours to keep generation cheap while refreshing
    # reasonably often as content changes.
    path(
        "sitemap.xml",
        cache_page(43200)(sitemap),
        {"sitemaps": _sitemaps},
        name="sitemap",
    ),
    path("", root_view, name="root"),
]


def safe_serve(request, path, document_root=None, show_indexes=False):
    if path.startswith("logs/"):
        raise Http404()
    return serve(
        request,
        path,
        document_root=document_root,
        show_indexes=show_indexes,
    )


if settings.ADMIN_DOMAIN in settings.ALLOWED_HOSTS:
    urlpatterns += [
        *admin_secure_media_urlpatterns,
        path(
            f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
            safe_serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

# The catch-all must be the absolute last route processed.
urlpatterns += api_v1_catch_all_urlpatterns
