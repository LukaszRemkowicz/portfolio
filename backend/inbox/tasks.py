# backend/inbox/tasks.py
import logging

from celery import shared_task

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from users.models import Profile, User

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
            if settings.SIMULATE_CONTACT_EMAILS:
                EmailHandler._log_email_simulation(contact_message)
                return

            EmailHandler._send_owner_notification(contact_message)
            EmailHandler._send_sender_confirmation(contact_message)
            logger.info(f"Email notifications sent for message ID={contact_message.id}")
        except Exception as e:
            logger.error(
                f"Failed to send email notifications for message ID={contact_message.id}: {e}"
            )

    @staticmethod
    def _send_owner_notification(contact_message: ContactMessage) -> None:
        subject: str = f"New Contact Message: {contact_message.subject}"
        message: str = f"""
                New contact message received:

                From: {contact_message.name} ({contact_message.email})
                Subject: {contact_message.subject}
                Message: {contact_message.message}

                Received at: {contact_message.created_at}
                Message ID: {contact_message.id}
                """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )

    @staticmethod
    def _send_sender_confirmation(contact_message: ContactMessage) -> None:
        context = EmailHandler._build_sender_confirmation_context()
        html_content = render_to_string("inbox/email/contact_auto_response.html", context)
        subject = "Message Received - Astrophotography Portfolio"

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_message.email],
            reply_to=[settings.CONTACT_EMAIL],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

    @staticmethod
    def _build_sender_confirmation_context() -> dict[str, str | int]:
        user = User.get_user()
        astro_profile = None
        if user is not None:
            astro_profile = user.profiles.filter(type=Profile.ProfileType.ASTRO).first()

        site_url = f"https://{settings.SITE_DOMAIN}"

        return {
            "portfolio_owner": settings.PROJECT_OWNER,
            "gallery_url": f"{site_url}/astrophotography",
            "instagram_url": getattr(astro_profile, "ig_url", "") or "",
            "facebook_url": getattr(astro_profile, "fb_url", "") or "",
            "astrobin_url": getattr(astro_profile, "astrobin_url", "") or "",
            "copyright_year": timezone.now().year,
        }

    @staticmethod
    def _log_email_simulation(contact_message: ContactMessage) -> None:
        owner_subject: str = f"New Contact Message: {contact_message.subject}"
        owner_message: str = f"""
                New contact message received:

                From: {contact_message.name} ({contact_message.email})
                Subject: {contact_message.subject}
                Message: {contact_message.message}

                Received at: {contact_message.created_at}
                Message ID: {contact_message.id}
                """
        sender_context = EmailHandler._build_sender_confirmation_context()
        sender_html = render_to_string("inbox/email/contact_auto_response.html", sender_context)

        logger.info("SIMULATE_CONTACT_EMAILS=True: Simulating contact email send.")
        logger.info(f"To: {[settings.CONTACT_EMAIL]}")
        logger.info(f"Subject: {owner_subject}")
        logger.info(f"Body: {owner_message}")
        logger.info(f"To: {[contact_message.email]}")
        logger.info("Subject: Message Received - Astrophotography Portfolio")
        logger.info(f"Body: {sender_html}")
        logger.info(f"Fake Email notifications sent for message ID={contact_message.id}")


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
