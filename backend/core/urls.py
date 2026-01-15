# backend/core/urls.py
"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

from .views import FeaturesEnabledView, api_404_view

# Admin site customization
admin.site.site_header = "Portfolio Administration"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"


# Base URL patterns (API endpoints)
urlpatterns = [
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("astrophotography.urls")),
    path("api/v1/", include("inbox.urls")),
    path("api/v1/whats-enabled/", FeaturesEnabledView.as_view(), name="whats-enabled"),
    path("api/v1/<path:path>", api_404_view),
]

# Add admin URLs and media serving if we're on admin subdomain
if settings.ADMIN_DOMAIN in settings.ALLOWED_HOSTS:
    urlpatterns += [
        path("", admin.site.urls),
    ]
    # Always serve media files on admin subdomain
    urlpatterns += [
        path(
            f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
