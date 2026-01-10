# backend/inbox/views.py
import logging
from typing import Any, Optional

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.throttling import ContactFormThrottle

from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .services import ContactSubmissionService

logger = logging.getLogger(__name__)

# Throttling handled by custom ContactFormThrottle with IP + email tracking (via DRF library)


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling contact messages with enhanced bot/DDoS protection.
    Throttling is applied by DRF library BEFORE validation (better for bot filtering).
    Frontend validation prevents valid users from being throttled on invalid submissions.
    """

    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]  # Create is public, other actions restricted below
    throttle_classes = [ContactFormThrottle]  # DRF handles throttling before validation

    def get_permissions(self):
        """
        Restrict list, retrieve, update, delete to authenticated users.
        Only create (contact form submission) is public.
        """
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_throttles(self):
        """Only throttle create action (contact form submissions)"""
        if self.action == "create":
            return [throttle() for throttle in self.throttle_classes]
        return super().get_throttles()  # Use default throttling for other actions (or none)

    def throttled(self, request: Request, wait: int) -> None:
        """Custom throttled response with user-friendly message"""
        raise Throttled(
            detail="You've submitted too many messages. Please wait 1 hour.",
            wait=wait,
        )

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return str(request.META.get("REMOTE_ADDR", "unknown"))

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new contact message with enhanced security checks.
        Note: Kill switch check is handled by ContactFormKillSwitchMiddleware before this view.
        Logic delegated to ContactSubmissionService.
        """
        client_ip = self.get_client_ip(request)
        contact_message = ContactSubmissionService.process_submission(request, client_ip)

        return Response(
            {
                "message": "Thank you! Your message has been sent successfully.",
                "id": contact_message.id,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_as_read(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Mark a contact message as read
        """
        contact_message: ContactMessage = self.get_object()
        contact_message.is_read = True
        contact_message.save()

        return Response({"message": "Message marked as read", "id": contact_message.id})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def unread_count(self, request: Request) -> Response:
        """
        Get count of unread messages
        """
        count: int = ContactMessage.objects.filter(is_read=False).count()
        return Response({"unread_count": count})
