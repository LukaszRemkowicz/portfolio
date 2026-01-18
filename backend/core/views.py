from typing import Any

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import LandingPageSettings


class FeaturesEnabledView(APIView):
    """
    Endpoint to check which features are currently enabled in the system.
    Returns a dictionary of enabled features.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        data: dict[str, bool] = {}

        # Get global settings
        settings = LandingPageSettings.objects.first()

        # If settings exist, use them. Otherwise default purely to True (safe fallback)
        if settings:
            data["programming"] = settings.programming_enabled
            data["contactForm"] = settings.contact_form_enabled
            data["travelHighlights"] = settings.travel_highlights_enabled
            data["lastimages"] = settings.lastimages_enabled
        else:
            # Default state if no settings object exists yet
            data["programming"] = True
            data["contactForm"] = True
            data["travelHighlights"] = True
            data["lastimages"] = True

        return Response(data)


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
