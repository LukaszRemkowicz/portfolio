# backend/inbox/middleware.py
import logging
from typing import Optional

from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import ContactFormSettings

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
        # Router creates: /api/v1/contact/ (list/create) and /api/v1/contact/{id}/ (detail/update/delete)
        # We only want to check the base endpoint for form submissions
        if request.method != "POST" or request.path != self.CONTACT_PATH:
            return None

        # Check if contact form is enabled
        try:
            settings: ContactFormSettings = ContactFormSettings.get_settings()
            if not settings.enabled:
                # Get client IP for logging
                x_forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    client_ip: str = x_forwarded_for.split(",")[0].strip()
                else:
                    client_ip = str(request.META.get("REMOTE_ADDR", "unknown"))

                logger.warning(
                    f"Contact form request blocked - form disabled. IP: {client_ip}, Path: {request.path}"
                )

                # Return HTTP 400 Bad Request as requested
                return JsonResponse(
                    {"message": "Contact form is currently disabled. Please try again later."},
                    status=400,
                )
        except Exception as error:
            # If there's an error accessing settings, log and allow request to continue
            # (fail open - better to allow submissions than block everything on error)
            logger.error(f"Error checking contact form settings in middleware: {error}")
            return None

        # Form is enabled, continue processing
        return None
