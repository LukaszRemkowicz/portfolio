# backend/inbox/services.py
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from rest_framework.exceptions import APIException

from django.utils import timezone

from common.utils.logging import sanitize_for_logging

from .models import ContactMessage
from .tasks import send_notification_email_task

logger = logging.getLogger(__name__)


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
                created_at__gte=timezone.now() - timedelta(minutes=5),
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

        # 1. Send email notification via Celery task
        send_notification_email_task.delay(contact_message.id)

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
