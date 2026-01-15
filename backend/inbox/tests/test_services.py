from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from inbox.models import ContactMessage
from inbox.services import (
    ContactMessageEmailService,
    ContactSubmissionService,
    DuplicateSubmission,
)
from inbox.tests.factories import ContactMessageFactory


@pytest.fixture
def mock_email_service() -> Generator[None, None, None]:
    """
    Override the autouse fixture from conftest.py to DO NOTHING.
    This allows us to test the actual service methods without them being mocked out.
    """
    yield


class TestContactMessageEmailService:
    @patch("inbox.services.send_mail")
    @patch("inbox.services.logger")
    def test_send_notification_email_success(
        self, mock_logger: MagicMock, mock_send_mail: MagicMock, contact_message: ContactMessage
    ) -> None:
        """Test successful email sending"""
        # Call the service method
        ContactMessageEmailService.send_notification_email(contact_message)

        # Verify send_mail was called with correct arguments
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        assert f"New Contact Message: {contact_message.subject}" in kwargs["subject"]
        assert contact_message.message in kwargs["message"]
        # Verify logger info was called
        mock_logger.info.assert_called_with(
            f"Email notification sent for message ID={contact_message.id}"
        )

    @patch("inbox.services.send_mail")
    @patch("inbox.services.logger")
    def test_send_notification_email_failure(
        self, mock_logger: MagicMock, mock_send_mail: MagicMock, contact_message: ContactMessage
    ) -> None:
        """Test failure handling when send_mail raises exception"""
        # Simulate send_mail raising an exception
        mock_send_mail.side_effect = Exception("SMTP Error")

        # Call the service method
        ContactMessageEmailService.send_notification_email(contact_message)

        # Verify error was logged
        mock_logger.error.assert_called_with(
            f"Failed to send email notification for message ID={contact_message.id}: SMTP Error"
        )

    @patch("threading.Thread")
    def test_send_notification_email_async(
        self, mock_thread_class: MagicMock, contact_message: ContactMessage
    ) -> None:
        """Test async wrapper starts a daemon thread"""
        # Call the async method
        ContactMessageEmailService.send_notification_email_async(contact_message)

        # Verify Thread was initialized with correct target and args
        mock_thread_class.assert_called_once_with(
            target=ContactMessageEmailService.send_notification_email,
            args=(contact_message,),
            daemon=True,
        )
        # Verify thread was started
        mock_thread_class.return_value.start.assert_called_once()


@pytest.mark.django_db
class TestContactSubmissionService:

    def test_check_duplicate_success(self, valid_contact_data: dict[str, str]) -> None:
        """Test that check_duplicate proceeds normally when no duplicate exists"""
        # Should not raise any exception
        ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    @patch("inbox.services.logger")
    def test_check_duplicate_raises_exception(
        self, mock_logger: MagicMock, valid_contact_data: dict[str, str]
    ) -> None:
        """Test that check_duplicate raises DuplicateSubmission when a duplicate exists"""
        ContactMessageFactory(**valid_contact_data)

        with pytest.raises(DuplicateSubmission):
            ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    @patch("inbox.services.ContactMessageEmailService.send_notification_email_async")
    def test_finalize_submission(
        self, mock_email: MagicMock, contact_message: ContactMessage
    ) -> None:
        """Test that finalize_submission sends email and logs success"""
        ContactSubmissionService.finalize_submission(contact_message, "127.0.0.1")
        mock_email.assert_called_once_with(contact_message)

    @patch("inbox.services.logger")
    def test_log_incoming_data_masking(self, mock_logger: MagicMock) -> None:
        """Test log masking for emails and long messages"""
        data = {
            "email": "test@example.com",
            "message": "A" * 11,
            "subject": "Short",
            "long_field": "X" * 101,
        }

        ContactSubmissionService.log_incoming_data(data, "127.0.0.1")

        # Check masked data in log call
        args, _ = mock_logger.info.call_args
        log_str = args[0]
        assert "te***@example.com" in log_str
        assert "<11 chars>" in log_str
        assert "X" * 100 + "..." in log_str

    @patch("inbox.services.logger")
    def test_log_incoming_data_malformed_email(self, mock_logger: MagicMock) -> None:
        """Test log masking for malformed email strings"""
        data = {"email": "not-an-email"}

        ContactSubmissionService.log_incoming_data(data, "127.0.0.1")

        args, _ = mock_logger.info.call_args
        assert "***" in args[0]
