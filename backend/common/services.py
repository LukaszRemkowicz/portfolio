import logging

from common.tasks import send_email_task

logger = logging.getLogger(__name__)


class EmailService:
    """
    Base email service providing common email utilities.

    This service handles the generic email sending infrastructure.
    App-specific email generation should be in their own services
    (e.g., LogAnalysisEmailService, ContactMessageEmailService).
    """

    @staticmethod
    def send_async(subject: str, html_content: str) -> None:
        """
        Dispatch email to async Celery task.

        This is the common interface for all email sending across the application.

        Args:
            subject: Email subject line
            html_content: Rendered HTML email body
        """
        logger.debug("Dispatching email to async task: %s", subject)
        send_email_task.delay(html_content=html_content, subject=subject)
