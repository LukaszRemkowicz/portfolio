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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.static import serve
import os

# Admin site customization
admin.site.site_header = 'Portfolio Administration'
admin.site.site_title = 'Portfolio Admin Portal'
admin.site.index_title = 'Welcome to Portfolio Admin Portal'

def debug_serve_media(request: HttpRequest, path: str, document_root: str) -> FileResponse:
    print(f"Serving media file: {path}")
    print(f"Document root: {document_root}")
    full_path = os.path.join(document_root, path)
    print(f"Full path: {full_path}")
    print(f"File exists: {os.path.exists(full_path)}")
    return serve(request, path, document_root)

# Base URL patterns (API endpoints)
urlpatterns = [
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('astrophotography.urls')),
    path('api/v1/', include('inbox.urls')),
]

# Add admin URLs and media serving if we're on admin subdomain
if settings.ADMIN_DOMAIN in settings.ALLOWED_HOSTS:
    urlpatterns += [
        path('', admin.site.urls),
    ]
    # Always serve media files on admin subdomain with debug info
    urlpatterns += [
        path('media/<path:path>', debug_serve_media, {'document_root': settings.MEDIA_ROOT}),
]
