"""
Shared views and utility endpoints for the core application.
"""
from typing import Any, cast

from django.http import Http404, HttpResponse
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

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
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def admin_dynamic_parler_css_view(request: Request) -> Response:
    """
    Returns dynamically generated CSS to hide the 'X' (delete) button
    for the configured default/fallback language in Django Admin.
    """
    default_lang = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", "en")

    css = f"""
    /* Dynamic Parler CSS generated for default language: {default_lang} */

    /* 
       RULE 1: Inactive Tab 
       Structure: <span class="available"><a href="?language={default_lang}">...</a> <a class="deletelink"></a></span>
       Target: .deletelink that is a sibling of the language link
    */
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .deletelink,
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .parler-delete {{
        display: none !important;
    }}

    /* 
       RULE 2: Active Tab 
       Structure: <input name="{default_lang}" ...> <span class="current">... <a class="deletelink"></a></span>
       Target: .deletelink inside the span that follows the input
    */
    .parler-language-tabs input[name="{default_lang}"] + span .deletelink,
    .parler-language-tabs input[name="{default_lang}"] + span .parler-delete {{
        display: none !important;
    }}
    """
    
    return HttpResponse(css, content_type="text/css")
