# backend/inbox/services.py
import logging
import threading
from typing import List

from django.conf import settings
from django.core.mail import send_mail

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

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email notification sent for message ID={contact_message.id}")
        except Exception as e:
            logger.error(f"Failed to send email notification for message ID={contact_message.id}: {e}")

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