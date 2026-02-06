# backend/inbox/tasks.py
import logging
from typing import List

from celery import shared_task

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from .models import ContactMessage

logger = logging.getLogger(__name__)


class EmailHandler:
    """
    Handler for sending email notifications related to contact messages.
    Moved to tasks.py to avoid circular imports and renamed to reflect
    its role as an infrastructure handler for background work.
    """

    @staticmethod
    def send_email(contact_message: ContactMessage) -> None:
        """
        Internal method to send the actual email notification.
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


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
)  # type: ignore[untyped-decorator]
def send_notification_email_task(self, contact_message_id: int) -> None:
    """
    Celery task to send email notification for a contact message.
    """
    try:
        contact_message = ContactMessage.objects.get(pk=contact_message_id)
        EmailHandler.send_email(contact_message)
    except ObjectDoesNotExist:
        logger.error(f"Message {contact_message_id} not found. Skipping email.")
    except Exception as exc:
        logger.exception(f"Error sending email for message {contact_message_id}")
        raise self.retry(exc=exc)
