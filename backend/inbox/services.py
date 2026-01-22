# backend/inbox/services.py
import logging
import threading
from typing import Any, Dict, List, Optional

from rest_framework.exceptions import APIException

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from core.utils.logging import sanitize_for_logging

from .models import ContactMessage

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

            if settings.DEBUG:
                logger.info("DEBUG=True: Simulating email send.")
                logger.info(f"To: {recipient_list}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body: {message}")
                logger.info(f"Fake Email notification sent for message ID={contact_message.id}")
                return

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
    def check_duplicate(validated_data: Dict[str, Any], client_ip: str) -> None:
        """
        Check for duplicate messages within a short timeframe.

        Args:
            validated_data: Dictionary of validated message data
            client_ip: The IP address of the client

        Raises:
            DuplicateSubmission: If duplicate message detected
        """
        # Sanitize IP for logging to prevent log injection
        safe_ip = sanitize_for_logging(client_ip)
        logger.info(f"Contact form submission attempt from IP: {safe_ip}")

        email: Optional[str] = validated_data.get("email")
        subject: Optional[str] = validated_data.get("subject")

        # Sanitize email and subject for logging
        safe_email = sanitize_for_logging(email) if email else ""
        safe_subject = sanitize_for_logging(subject) if subject else ""

        if email and subject:
            recent_duplicate: bool = ContactMessage.objects.filter(
                email=email,
                subject=subject,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=5),
            ).exists()
            if recent_duplicate:
                logger.warning(
                    f"Duplicate message from {safe_email} w/ subject '{safe_subject}' "
                    f"at IP {safe_ip}"
                )
                raise DuplicateSubmission()

    @staticmethod
    def finalize_submission(contact_message: ContactMessage, client_ip: str) -> None:
        """
        Handle post-persistence tasks for a contact message.

        Args:
            contact_message: The created ContactMessage instance
            client_ip: The IP address of the client
        """
        safe_ip = sanitize_for_logging(client_ip)
        safe_email = sanitize_for_logging(contact_message.email) if contact_message.email else ""

        # 1. Send email notification
        ContactMessageEmailService.send_notification_email_async(contact_message)

        logger.info(
            f"Contact message created: ID={contact_message.id}, Email={safe_email}, IP={safe_ip}"
        )

    @staticmethod
    def log_incoming_data(data: Dict[str, Any], client_ip: str) -> None:
        """Helper to log sanitized incoming data"""
        sanitized_data: Dict[str, Any] = {}
        for key, value in data.items():
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
        safe_ip = sanitize_for_logging(client_ip)
        logger.info(f"Contact form data received from IP {safe_ip}: {sanitized_data}")
