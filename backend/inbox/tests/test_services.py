# backend/inbox/tests/test_services.py
from unittest.mock import patch

import pytest

from inbox.models import ContactMessage
from inbox.services import ContactMessageEmailService


@pytest.fixture
def contact_message():
    return ContactMessage(
        name="Test Sender",
        email="sender@example.com",
        subject="Test Subject",
        message="Test Message Body",
        id=123,
    )


@pytest.fixture
def mock_email_service():
    """
    Override the autouse fixture from conftest.py to DO NOTHING.
    This allows us to test the actual service methods without them being mocked out.
    """
    yield


class TestContactMessageEmailService:
    @patch("inbox.services.send_mail")
    @patch("inbox.services.logger")
    def test_send_notification_email_success(self, mock_logger, mock_send_mail, contact_message):
        """Test successful email sending"""
        # Call the service method
        ContactMessageEmailService.send_notification_email(contact_message)

        # Verify send_mail was called with correct arguments
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        assert "New Contact Message: Test Subject" in kwargs["subject"]
        assert "Test Message Body" in kwargs["message"]
        # Verify logger info was called
        mock_logger.info.assert_called_with(
            f"Email notification sent for message ID={contact_message.id}"
        )

    @patch("inbox.services.send_mail")
    @patch("inbox.services.logger")
    def test_send_notification_email_failure(self, mock_logger, mock_send_mail, contact_message):
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
    def test_send_notification_email_async(self, mock_thread_class, contact_message):
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
