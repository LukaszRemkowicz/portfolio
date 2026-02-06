# backend/inbox/tests/test_services.py
import pytest
from pytest_mock import MockerFixture

from django.test import override_settings

from inbox.models import ContactMessage
from inbox.services import ContactMessageEmailService, ContactSubmissionService, DuplicateSubmission
from inbox.tests.factories import ContactMessageFactory


class TestContactMessageEmailService:
    def test_send_notification_email_success(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test successful email sending"""
        mock_send_mail = mocker.patch("inbox.services.send_mail")
        mock_logger = mocker.patch("inbox.services.logger")

        # Call the service method
        ContactMessageEmailService.send_notification_email(contact_message)

        # Verify send_mail was called with correct arguments
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        assert f"New Contact Message: {contact_message.subject}" in kwargs["subject"]
        assert contact_message.message in kwargs["message"]
        # Verify logger info was called
        mock_logger.info.assert_any_call(
            f"Email notification sent for message ID={contact_message.id}"
        )

    def test_send_notification_email_debug_simulation(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test that email is simulated (logged) but NOT sent when DEBUG=True"""
        mock_send_mail = mocker.patch("inbox.services.send_mail")
        mock_logger = mocker.patch("inbox.services.logger")

        with override_settings(DEBUG=True):
            # Call the service method
            ContactMessageEmailService.send_notification_email(contact_message)

        # Verify send_mail was NOT called
        mock_send_mail.assert_not_called()

        # Verify logger.info was called with simulation messages
        mock_logger.info.assert_any_call("DEBUG=True: Simulating email send.")
        mock_logger.info.assert_any_call(
            f"Fake Email notification sent for message ID={contact_message.id}"
        )

    def test_send_notification_email_failure(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test failure handling when send_mail raises exception"""
        mock_send_mail = mocker.patch("inbox.services.send_mail")
        mock_logger = mocker.patch("inbox.services.logger")

        # Simulate send_mail raising an exception
        mock_send_mail.side_effect = Exception("SMTP Error")

        # Call the service method
        ContactMessageEmailService.send_notification_email(contact_message)

        # Verify error was logged
        mock_logger.error.assert_called_with(
            f"Failed to send email notification for message ID={contact_message.id}: SMTP Error"
        )

    def test_send_notification_email_async(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test async wrapper starts a daemon thread"""
        mock_thread_class = mocker.patch("threading.Thread")

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

    def test_check_duplicate_raises_exception(
        self, mocker: MockerFixture, valid_contact_data: dict[str, str]
    ) -> None:
        """Test that check_duplicate raises DuplicateSubmission when a duplicate exists"""
        mocker.patch("inbox.services.logger")
        ContactMessageFactory(**valid_contact_data)

        with pytest.raises(DuplicateSubmission):
            ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    def test_finalize_submission(
        self, mocker: MockerFixture, contact_message: ContactMessage
    ) -> None:
        """Test that finalize_submission sends email and logs success"""
        mock_email = mocker.patch(
            "inbox.services.ContactMessageEmailService.send_notification_email_async"
        )

        ContactSubmissionService.finalize_submission(contact_message, "127.0.0.1")
        mock_email.assert_called_once_with(contact_message)

    def test_log_incoming_data_masking(self, mocker: MockerFixture) -> None:
        """Test log masking for emails and long messages"""
        mock_logger = mocker.patch("inbox.services.logger")

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

    def test_log_incoming_data_malformed_email(self, mocker: MockerFixture) -> None:
        """Test log masking for malformed email strings"""
        mock_logger = mocker.patch("inbox.services.logger")
        data = {"email": "not-an-email"}

        ContactSubmissionService.log_incoming_data(data, "127.0.0.1")

        args, _ = mock_logger.info.call_args
        assert "***" in args[0]
