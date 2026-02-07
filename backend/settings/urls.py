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
from django.urls import include, path
from django.views.static import serve

from core.views import SettingsView, api_404_view, health_check_view

admin.site.site_header = "Portfolio Administration"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"


urlpatterns = [
    path("v1/", include("users.urls")),
    path("v1/", include("astrophotography.urls")),
    path("v1/", include("inbox.urls")),
    path("v1/settings/", SettingsView.as_view(), name="settings"),
    path("health", health_check_view, name="health"),
    path("v1/<path:path>", api_404_view),
    path("select2/", include("django_select2.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("", include("translation.urls")),
]

if settings.ADMIN_DOMAIN in settings.ALLOWED_HOSTS:
    urlpatterns += [
        path("", admin.site.urls),
    ]
    urlpatterns += [
        path(
            f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
