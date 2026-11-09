import logging
from collections.abc import Iterable

from django.conf import settings
from django.core.mail import EmailMessage

from common.ssr_cache import invalidate_frontend_ssr_cache

logger = logging.getLogger(__name__)


def send_email_task(html_content: str, subject: str) -> None:
    """
    Send HTML email notification (run via common.background.submit, retries=3).

    Args:
        html_content: Rendered HTML email body
        subject: Email subject line
    """
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_EMAIL],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)

    logger.info("Email sent: %s", subject)


def invalidate_frontend_ssr_cache_task(tags: Iterable[str]) -> bool:
    return invalidate_frontend_ssr_cache(tags)
