import logging
from abc import ABC, abstractmethod

from django.template.loader import render_to_string

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


class BaseEmailService(ABC):
    """
    Abstract base class for email services using Template Method pattern.

    Subclasses must implement:
    - get_subject()
    - get_context()
    - get_template_name()
    """

    def send_email(self) -> None:
        """
        Template method defining the email sending workflow.

        This method orchestrates the email generation and sending process:
        1. Generate subject
        2. Generate context
        3. Render template
        4. Send email
        """
        subject = self.get_subject()
        context = self.get_context()
        html_content = self.render_template(context)
        self.dispatch_email(subject, html_content)

    @abstractmethod
    def get_subject(self) -> str:
        """Generate email subject line."""
        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> dict:
        """Generate template context dictionary."""
        raise NotImplementedError

    @abstractmethod
    def get_template_name(self) -> str:
        """Return path to email template."""
        raise NotImplementedError

    def render_template(self, context: dict) -> str:
        """Render email template with context."""
        template_name = self.get_template_name()
        return render_to_string(template_name, context)

    def dispatch_email(self, subject: str, html_content: str) -> None:
        """Dispatch email to async task."""
        EmailService.send_async(subject, html_content)
