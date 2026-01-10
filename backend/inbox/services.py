# backend/inbox/services.py
import logging
import threading
from typing import Any, Dict, List, Optional

from rest_framework.exceptions import APIException
from rest_framework.request import Request

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import ContactMessage
from .serializers import ContactMessageSerializer

logger = logging.getLogger(__name__)


class ContactMessageEmailService:
    """
    Service for handling email notifications related to contact messages.
    Separates email logic from views for better testability and reusability.
    """

    @staticmethod
    def send_notification_email(contact_message: ContactMessage) -> None:
        """
        Send email notification for a new contact message.
        Called asynchronously to prevent blocking the request.
        """
        try:
            subject: str = f"New Contact Message: {contact_message.subject}"
            message: str = f"""
                New contact message received:

                From: {contact_message.name} ({contact_message.email})
                Subject: {contact_message.subject}
                Message: {contact_message.message}

                Received at: {contact_message.created_at}
                Message ID: {contact_message.id}
                """

            from_email: str = settings.DEFAULT_FROM_EMAIL
            recipient_list: List[str] = [settings.CONTACT_EMAIL]

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email notification sent for message ID={contact_message.id}")
        except Exception as e:
            logger.error(
                f"Failed to send email notification for message ID={contact_message.id}: {e}"
            )

    @staticmethod
    def send_notification_email_async(contact_message: ContactMessage) -> None:
        """
        Send email notification asynchronously using threading.
        This prevents email sending from blocking the HTTP request.
        TODO: Migrate to Celery when email volume > 50/day or retry/reliability needed.
        """
        email_thread: threading.Thread = threading.Thread(
            target=ContactMessageEmailService.send_notification_email,
            args=(contact_message,),
            daemon=True,
        )
        email_thread.start()


class PayloadTooLarge(APIException):
    status_code = 413
    default_detail = "Request payload too large."
    default_code = "request_too_large"


class DuplicateSubmission(APIException):
    status_code = 429
    default_detail = "Please wait before submitting another message with the same subject."
    default_code = "duplicate_submission"


class ContactSubmissionService:
    """
    Service for handling contact form submissions.
    Encapsulates validation, spam checks, and persistence logic.
    """

    @staticmethod
    def process_submission(request: Request, client_ip: str) -> ContactMessage:
        """
        Process a contact form submission request.

        Args:
            request: The DRF Request object
            client_ip: The IP address of the client

        Returns:
            ContactMessage: The created message instance

        Raises:
            PayloadTooLarge: If content length > 10000 bytes
            DuplicateSubmission: If duplicate message detected
            ValidationError: If serializer validation fails
        """
        logger.info(f"Contact form submission attempt from IP: {client_ip}")

        # 1. Log sanitized incoming data
        ContactSubmissionService.log_incoming_data(request, client_ip)

        # 2. Check request size limit
        content_length: Optional[str] = request.META.get("CONTENT_LENGTH")
        if content_length:
            try:
                content_length_int: int = int(content_length)
                if content_length_int > 10000:
                    logger.warning(
                        f"Request too large: {content_length_int} bytes from {client_ip}"
                    )
                    raise PayloadTooLarge()
            except (ValueError, TypeError):
                pass

        # 3. Validate data using serializer
        serializer = ContactMessageSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if hasattr(serializer, "errors"):
                logger.error(
                    f"Contact form validation failed for IP {client_ip}: "
                    f"Errors: {serializer.errors}, Data keys: {list(request.data.keys())}"
                )
            else:
                logger.error(f"Contact form validation failed for IP {client_ip}: {str(e)}")
            raise

        # 4. Extract validated data
        email: Optional[str] = serializer.validated_data.get("email")
        subject: Optional[str] = serializer.validated_data.get("subject")

        # 5. Check for duplicate messages
        if email and subject:
            recent_duplicate: bool = ContactMessage.objects.filter(
                email=email,
                subject=subject,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=5),
            ).exists()
            if recent_duplicate:
                logger.warning(
                    f"Duplicate message from {email} w/ subject '{subject}' at IP {client_ip}"
                )
                raise DuplicateSubmission()

        # 6. Save message
        contact_message: ContactMessage = serializer.save()

        # 7. Send email notification
        ContactMessageEmailService.send_notification_email_async(contact_message)

        logger.info(
            f"Contact message created: ID={contact_message.id}, Email={email}, IP={client_ip}"
        )
        return contact_message

    @staticmethod
    def log_incoming_data(request: Request, client_ip: str) -> None:
        """Helper to log sanitized incoming data"""
        incoming_data: Dict[str, Any] = (
            dict(request.data) if hasattr(request.data, "__dict__") else request.data
        )
        sanitized_data: Dict[str, Any] = {}
        for key, value in incoming_data.items():
            if key == "message":
                sanitized_data[key] = f"<{len(str(value))} chars>"
            elif key == "email":
                email_str = str(value)
                if "@" in email_str:
                    parts = email_str.split("@")
                    sanitized_data[key] = f"{parts[0][:2]}***@{parts[1]}"
                else:
                    sanitized_data[key] = "***"
            else:
                sanitized_data[key] = f"{str(value)[:100]}..." if len(str(value)) > 100 else value
        logger.info(f"Contact form data received from IP {client_ip}: {sanitized_data}")
