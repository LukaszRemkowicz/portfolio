from django.urls import include, path

from astrophotography.views import AstroImageAdminSecureMediaView
from core.views import (
    GenericAdminSecureMediaView,
    SettingsView,
    api_404_view,
    health_check_view,
    v1_root_view,
)
from monitoring.views import LogAnalysisAdminSecureMediaView, SitemapAnalysisTaskStatusView

API_V1_PATH = "v1/"

# Core API routes for version 1
api_v1_base_urlpatterns = [
    path(API_V1_PATH, v1_root_view, name="v1-root"),
    path(API_V1_PATH, include("users.urls")),
    path(API_V1_PATH, include("astrophotography.urls")),
    path(API_V1_PATH, include("inbox.urls")),
    path(API_V1_PATH + "settings/", SettingsView.as_view(), name="settings"),
    path(API_V1_PATH + "health", health_check_view, name="health-v1"),
]

# Secure media logic intended for the Admin domain
admin_secure_media_urlpatterns = [
    # Dedicated Admin Media URLs
    path(
        f"{API_V1_PATH}admin/media/astrophotography/astroimage/<str:pk>/<str:field_name>/",
        AstroImageAdminSecureMediaView.as_view(),
        name="admin-astroimage-secure-media",
    ),
    path(
        f"{API_V1_PATH}admin/media/monitoring/loganalysis/<str:pk>/<str:field_name>/",
        LogAnalysisAdminSecureMediaView.as_view(),
        name="admin-loganalysis-secure-media",
    ),
    path(
        f"{API_V1_PATH}admin/monitoring/sitemap-task-status/<str:task_id>/",
        SitemapAnalysisTaskStatusView.as_view(),
        name="admin-sitemap-analysis-task-status",
    ),
    # Universal Admin Media Fallback
    path(
        f"{API_V1_PATH}admin/media/<str:app_label>/<str:model_name>/<str:pk>/<str:field_name>/",
        GenericAdminSecureMediaView.as_view(),
        name="admin-generic-secure-media",
    ),
]

# Final catch-all for undefined version 1 paths
api_v1_catch_all_urlpatterns = [
    path(f"{API_V1_PATH}<path:path>", api_404_view),
]
