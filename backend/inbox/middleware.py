# backend/inbox/middleware.py
import logging
from typing import Optional

from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from core.models import LandingPageSettings

logger = logging.getLogger(__name__)


class ContactFormKillSwitchMiddleware(MiddlewareMixin):
    """
    Middleware to check if contact form is enabled before processing requests.
    Acts as a kill switch - blocks all contact form requests if disabled.
    Should be placed early in MIDDLEWARE list for maximum efficiency.
    """

    # Path to check (contact form endpoint)
    # DRF DefaultRouter always creates URLs with trailing slashes: /api/v1/contact/
    CONTACT_PATH = "/api/v1/contact/"

    def process_request(self, request: HttpRequest) -> Optional[JsonResponse]:
        """
        Check if request is to contact form endpoint and if form is enabled.
        Returns JsonResponse if form is disabled, None to continue processing.

        Note: DRF DefaultRouter creates consistent URLs with trailing slashes.
        We check for the exact router-created path: /api/v1/contact/
        """
        # Only check POST requests to exact contact endpoint
        # Router creates: /api/v1/contact/ (list/create)
        # and /api/v1/contact/{id}/ (detail/update/delete)
        # We only want to check the base endpoint for form submissions
        if request.method != "POST" or request.path != self.CONTACT_PATH:
            return None

        # Check if contact form is enabled
        settings = LandingPageSettings.load()
        if not settings.contact_form_enabled:
            logger.warning(f"Contact form request blocked - form disabled. Path: {request.path}")

            # Return HTTP 400 Bad Request as requested
            return JsonResponse(
                {"message": "Contact form is currently disabled. Please try again later."},
                status=400,
            )

        # Form is enabled, continue processing
        return None
