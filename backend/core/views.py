from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from inbox.models import ContactFormSettings
from programming.models import ProgrammingPageConfig


class FeaturesEnabledView(APIView):
    """
    Endpoint to check which features are currently enabled in the system.
    Returns a dictionary of enabled features.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        data: dict[str, bool] = {}

        # Check ProgrammingPageConfig
        prog_config = ProgrammingPageConfig.get_config()
        if prog_config and prog_config.enabled:
            data["programming"] = True

        # Check ContactFormSettings
        contact_settings = ContactFormSettings.get_settings()
        if contact_settings and contact_settings.enabled:
            data["contactForm"] = True

        return Response(data)
