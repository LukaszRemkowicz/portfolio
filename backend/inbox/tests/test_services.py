# backend/inbox/tests/test_services.py
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from django.test import override_settings

from inbox.models import ContactMessage
from inbox.services import ContactSubmissionService, DuplicateSubmission
from inbox.tasks import EmailHandler
from inbox.tests.factories import ContactMessageFactory


class TestEmailHandler:
    def test_send_email_success(
        self,
        mock_inbox_send_mail: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test successful email sending"""

        # Call the service method
        EmailHandler.send_email(contact_message)

        # Verify send_mail was called with correct arguments
        mock_inbox_send_mail.assert_called_once()
        args, kwargs = mock_inbox_send_mail.call_args
        assert f"New Contact Message: {contact_message.subject}" in kwargs["subject"]
        assert contact_message.message in kwargs["message"]
        # Verify logger info was called
        mock_inbox_logger.info.assert_any_call(
            f"Email notification sent for message ID={contact_message.id}"
        )

    def test_send_notification_email_debug_simulation(
        self,
        mock_inbox_send_mail: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test that email is simulated (logged) but NOT sent when DEBUG=True"""

        with override_settings(DEBUG=True):
            # Call the handler method
            EmailHandler.send_email(contact_message)

        # Verify mock_inbox_send_mail was NOT called
        mock_inbox_send_mail.assert_not_called()

        # Verify logger.info was called with simulation messages
        mock_inbox_logger.info.assert_any_call("DEBUG=True: Simulating email send.")
        mock_inbox_logger.info.assert_any_call(
            f"Fake Email notification sent for message ID={contact_message.id}"
        )

    def test_send_email_failure(
        self,
        mock_inbox_send_mail: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test failure handling when send_mail raises exception"""

        # Simulate send_mail raising an exception
        mock_inbox_send_mail.side_effect = Exception("SMTP Error")

        # Call the service method
        EmailHandler.send_email(contact_message)

        # Verify error was logged
        mock_inbox_logger.error.assert_called_with(
            f"Failed to send email notification for message ID={contact_message.id}: SMTP Error"
        )


@pytest.mark.django_db
class TestContactSubmissionService:

    def test_check_duplicate_success(self, valid_contact_data: dict[str, str]) -> None:
        """Test that check_duplicate proceeds normally when no duplicate exists"""
        # Should not raise any exception
        ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    def test_check_duplicate_raises_exception(
        self,
        mock_inbox_service_logger: MagicMock,
        valid_contact_data: dict[str, str],
    ) -> None:
        """Test that check_duplicate raises DuplicateSubmission when a duplicate exists"""
        ContactMessageFactory(**valid_contact_data)

        with pytest.raises(DuplicateSubmission):
            ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    def test_finalize_submission(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test that finalize_submission triggers Celery task and logs success"""
        mock_task_delay = mocker.patch("inbox.services.send_notification_email_task.delay")

        ContactSubmissionService.finalize_submission(contact_message, "127.0.0.1")
        mock_task_delay.assert_called_once_with(contact_message.id)

    def test_log_incoming_data_masking(self, mock_inbox_service_logger: MagicMock) -> None:
        """Test log masking for emails and long messages"""
        data = {
            "email": "test@example.com",
            "message": "A" * 11,
            "subject": "Short",
            "long_field": "X" * 101,
        }

        ContactSubmissionService.log_incoming_data(data, "127.0.0.1")

        # Check masked data in log call
        args, _ = mock_inbox_service_logger.info.call_args
        log_str = args[0]
        assert "te***@example.com" in log_str
        assert "<11 chars>" in log_str
        assert "X" * 100 + "..." in log_str

    def test_log_incoming_data_malformed_email(self, mock_inbox_service_logger: MagicMock) -> None:
        """Test log masking for malformed email strings"""
        data = {"email": "not-an-email"}

        ContactSubmissionService.log_incoming_data(data, "127.0.0.1")

        args, _ = mock_inbox_service_logger.info.call_args
        assert "***" in args[0]
