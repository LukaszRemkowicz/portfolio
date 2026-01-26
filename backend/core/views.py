from typing import Any

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
        from typing import cast

        # Override get_object to return the singleton or raise 404
        obj = self.get_queryset().last()
        if not obj:
            from django.http import Http404

            raise Http404("Landing Page Settings not initialized.")
        return cast(LandingPageSettings, obj)


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
