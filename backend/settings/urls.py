"""
URL Configuration for the core application.

This file defines the main routing table for the project, including:
- Admin site URLs (when current host matches ADMIN_DOMAIN)
- Third-party integrations (Select2, CKEditor 5)
- Dynamic CSS for Parler-based admin translations
- Media file serving (on admin domain)
"""

from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.views.generic import RedirectView
from django.views.static import serve

from astrophotography.views import AstroImageAdminSecureMediaView
from core.views import GenericAdminSecureMediaView
from shop.views import ShopAstroImageLookupView

admin.site.site_header = "Portfolio Administration"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"

urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path(
        "api/v1/shop/image-lookup/",
        ShopAstroImageLookupView.as_view(),
        name="shop-image-lookup",
    ),
    path("", include("translation.urls")),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/admin/")),
]


def safe_serve(request, path, document_root=None, show_indexes=False):
    host = request.get_host().split(":")[0]
    allowed_prefixes = (
        "backgrounds/",
        "avatars/",
        "about_me_images/",
        "images/",
        "thumbnails/",
        "shop/",
        "programming/",
    )
    blocked_prefixes = ("logs/",)

    if host != settings.ADMIN_DOMAIN:
        raise Http404()

    if any(segment in {".", ".."} for segment in path.split("/")):
        raise Http404()

    if path.startswith(blocked_prefixes) or not path.startswith(allowed_prefixes):
        raise Http404()

    private_image_path = path.startswith("images/") and not path.startswith(
        ("images/thumbnail/", "images/detail/")
    )
    if private_image_path:
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False) or not getattr(user, "is_staff", False):
            raise Http404()

    response = serve(
        request,
        path,
        document_root=document_root,
        show_indexes=show_indexes,
    )
    if private_image_path:
        patch_cache_control(response, private=True, no_store=True, max_age=0)
        patch_vary_headers(response, ("Cookie",))
    return response


# Secure media for the admin: signed URLs, staff only.
admin_secure_media_urlpatterns = [
    path(
        "v1/admin/media/astrophotography/astroimage/<str:pk>/<str:field_name>/",
        AstroImageAdminSecureMediaView.as_view(),
        name="admin-astroimage-secure-media",
    ),
    path(
        "v1/admin/media/<str:app_label>/<str:model_name>/<str:pk>/<str:field_name>/",
        GenericAdminSecureMediaView.as_view(),
        name="admin-generic-secure-media",
    ),
]

if settings.ADMIN_DOMAIN in settings.ALLOWED_HOSTS:
    urlpatterns += [
        *admin_secure_media_urlpatterns,
        path(
            f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
            safe_serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
