"""
Shared views and utility endpoints for the core application.
"""

from typing import Any, cast

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from django.http import Http404
from django.shortcuts import render

from core.models import LandingPageSettings
from core.serializers import LandingPageSettingsSerializer


class SettingsView(generics.RetrieveAPIView):
    """
    Endpoint to fetch global application settings.
    - 'features': Boolean flags for enabled system modules.
    - 'meteors': Configuration for the shooting stars effect.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LandingPageSettingsSerializer
    queryset = LandingPageSettings.objects.all()

    def get_object(self) -> LandingPageSettings:
        """
        Returns the singleton LandingPageSettings instance or raises 404.
        """
        obj = self.get_queryset().last()
        if not obj:
            raise Http404("Landing Page Settings not initialized.")
        return cast(LandingPageSettings, obj)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health_check_view(request: Request) -> Response:
    """
    Simple health check endpoint returning 200 OK.
    """
    return Response({"status": "healthy"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def root_view(request: Request) -> Any:
    """
    Root view for all domains.
    - ADMIN_DOMAIN: Redirects to /admin/
    - Others: Redirects to SITE_DOMAIN (FE main page)
    """
    from django.conf import settings
    from django.shortcuts import redirect

    host = request.get_host().split(":")[0]  # Remove port if present
    if host == settings.ADMIN_DOMAIN:
        return redirect("admin:index")

    return redirect(f"https://{settings.SITE_DOMAIN}/")


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def v1_root_view(request: Request) -> Any:
    """
    API v1 root greetings page with a pretty template.
    """
    return render(request, "core/api_v1_greetings.html")


@api_view(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@permission_classes([permissions.AllowAny])
def api_404_view(request: Request, *args: Any, **kwargs: Any) -> Response:
    """
    Catch-all view for unmatched API endpoints.
    Ensures 404 Not Found is returned as JSON instead of falling through to admin.
    """
    return Response(
        {"detail": f"Endpoint '{request.path}' not found."},
        status=status.HTTP_404_NOT_FOUND,
    )
