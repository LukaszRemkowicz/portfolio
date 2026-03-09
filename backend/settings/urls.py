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
from django.http import Http404
from django.urls import include, path
from django.views.static import serve

from core.views import root_view

from .api_urls import (
    admin_secure_media_urlpatterns,
    api_v1_base_urlpatterns,
    api_v1_catch_all_urlpatterns,
)

admin.site.site_header = "Portfolio Administration"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"


urlpatterns = [
    *api_v1_base_urlpatterns,
    path("select2/", include("django_select2.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("", include("translation.urls")),
    path("admin/", admin.site.urls),
    path("", root_view, name="root"),
]


def safe_serve(*args, **kwargs):
    if "logs/" in args[0].path or "images/" in args[0].path:
        raise Http404()
    return serve(*args, **kwargs)


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
