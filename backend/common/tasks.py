import logging

import sentry_sdk
from celery import shared_task

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
)  # type: ignore[untyped-decorator]
def send_email_task(self, html_content: str, subject: str) -> None:
    """
    Celery task to send HTML email notification.

    Args:
        html_content: Rendered HTML email body
        subject: Email subject line
    """
    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

        logger.info("Email sent: %s", subject)
    except Exception as exc:
        logger.exception("Failed to send email: %s", subject)
        sentry_sdk.capture_exception(exc)
        raise self.retry(exc=exc)
