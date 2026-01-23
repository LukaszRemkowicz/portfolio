# backend/inbox/views.py
import logging
from typing import Any, NoReturn, Optional

from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from core.throttling import ContactFormThrottle

from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .services import ContactSubmissionService, PayloadTooLarge

logger = logging.getLogger(__name__)

# Throttling handled by custom ContactFormThrottle with IP + email tracking (via DRF library)


class ContactMessageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for handling contact messages with enhanced bot/DDoS protection.
    Throttling is applied by DRF library BEFORE validation (better for bot filtering).
    Frontend validation prevents valid users from being throttled on invalid submissions.
    """

    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]  # Publicly accessible for contact form submissions
    throttle_classes = [ContactFormThrottle]  # DRF handles throttling before validation

    def throttled(self, request: Request, wait: float) -> NoReturn:
        """Custom throttled response with user-friendly message"""
        # Create exception without 'wait' arg to prevent DRF from appending
        # "Expected available in..." to the details.
        exc = Throttled(
            detail="You've submitted too many messages. Please wait 1 hour to send another one."
        )
        # Manually set wait so Retry-After header is still populated by handler
        setattr(exc, "wait", wait)
        raise exc

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return str(request.META.get("REMOTE_ADDR", "unknown"))

    def _check_payload_size(self, request: Request, client_ip: str) -> None:
        """Check if request payload size exceeds limit"""
        content_length: Optional[str] = request.META.get("CONTENT_LENGTH")
        if content_length:
            try:
                content_length_int: int = int(content_length)
                if content_length_int > 10000:
                    safe_ip = client_ip.replace("\n", "").replace("\r", "")
                    logger.warning(f"Request too large: {content_length_int} bytes from {safe_ip}")
                    raise PayloadTooLarge()
            except (ValueError, TypeError):
                safe_ip = client_ip.replace("\n", "").replace("\r", "")
                logger.debug(f"Invalid CONTENT_LENGTH from {safe_ip}")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new contact message with enhanced security checks.
        Note: Kill switch check is handled by ContactFormKillSwitchMiddleware before this view.
        Logic delegated to ContactSubmissionService.
        """
        client_ip = self.get_client_ip(request)

        # 1. Check request size limit (first, to reject large requests before processing)
        self._check_payload_size(request, client_ip)

        # 2. Validate data using serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. Log sanitized incoming data
        ContactSubmissionService.log_incoming_data(serializer.validated_data, client_ip)

        # 4. Check for duplicates
        ContactSubmissionService.check_duplicate(serializer.validated_data, client_ip)

        # 5. Save message
        contact_message = serializer.save()

        # 6. Finalize submission (email, etc.)
        ContactSubmissionService.finalize_submission(contact_message, client_ip)

        return Response(
            {
                "message": "Thank you! Your message has been sent successfully.",
                "id": contact_message.id,
            },
            status=status.HTTP_201_CREATED,
        )
