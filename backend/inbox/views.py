# backend/inbox/views.py
import logging
from typing import Any, Optional

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django.utils import timezone

from core.throttling import ContactFormThrottle

from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .services import ContactMessageEmailService

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
    permission_classes = [AllowAny]
    throttle_classes = [ContactFormThrottle]  # DRF handles throttling before validation

    def throttled(self, request: Request, wait: int) -> None:
        """Custom throttled response with user-friendly message"""
        raise Throttled(
            detail="You've submitted too many messages recently. Please wait up to 1 hour before trying again.",
            wait=wait,
        )

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        ip: str
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = str(request.META.get("REMOTE_ADDR", "unknown"))
        return ip

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new contact message with enhanced security checks
        """
        client_ip: str = self.get_client_ip(request)
        logger.info(f"Contact form submission attempt from IP: {client_ip}")
        
        # Log incoming data (sanitized for security - no sensitive content)
        incoming_data: dict = dict(request.data) if hasattr(request.data, "__dict__") else request.data
        sanitized_data: dict = {}
        for k, v in incoming_data.items():
            if k == "message":
                # Log message length only, not content
                sanitized_data[k] = f"<{len(str(v))} chars>"
            elif k == "email":
                # Log email domain only for privacy
                email_str = str(v)
                if "@" in email_str:
                    parts = email_str.split("@")
                    sanitized_data[k] = f"{parts[0][:2]}***@{parts[1]}"
                else:
                    sanitized_data[k] = "***"
            else:
                sanitized_data[k] = f"{str(v)[:100]}..." if len(str(v)) > 100 else v
        logger.info(f"Contact form data received from IP {client_ip}: {sanitized_data}")
        
        # Check request size limit (prevent DoS via large payloads)
        content_length: Optional[str] = request.META.get("CONTENT_LENGTH")
        if content_length:
            try:
                content_length_int: int = int(content_length)
                if content_length_int > 10000:
                    logger.warning(f"Request too large: {content_length_int} bytes from {client_ip}")
                    return Response(
                        {"message": "Request payload too large."},
                        status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    )
            except (ValueError, TypeError):
                pass

        # Validate
        # Note: Throttling already happened via DRF's throttle_classes (before validation)
        # This is intentional - library handles bot filtering, frontend prevents user throttling on invalid data
        serializer: ContactMessageSerializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log validation errors in detail
            if hasattr(serializer, "errors"):
                logger.error(
                    f"Contact form validation failed for IP {client_ip}: "
                    f"Errors: {serializer.errors}, Data keys: {list(incoming_data.keys())}"
                )
            else:
                logger.error(f"Contact form validation failed for IP {client_ip}: {str(e)}")
            raise  # Re-raise to let DRF handle the 400 response

        # Extract validated data
        email: Optional[str] = serializer.validated_data.get("email")
        subject: Optional[str] = serializer.validated_data.get("subject")

        # Check for duplicate messages (same email + subject in last 5 minutes) before saving
        if email and subject:
            recent_duplicate: bool = ContactMessage.objects.filter(
                email=email, subject=subject, created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
            ).exists()
            if recent_duplicate:
                logger.warning(f"Duplicate message attempt from {email} with subject '{subject}' at IP {client_ip}")
                return Response(
                    {"message": "Please wait before submitting another message with the same subject."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        # Save message
        contact_message: ContactMessage = serializer.save()

        # Send email notification asynchronously (prevent email DoS)
        ContactMessageEmailService.send_notification_email_async(contact_message)

        # Log successful submission
        logger.info(f"Contact message created: ID={contact_message.id}, Email={email}, IP={self.get_client_ip(request)}")

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
