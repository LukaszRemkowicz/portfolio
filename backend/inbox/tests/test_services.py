# backend/inbox/tests/test_services.py
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from inbox.models import ContactMessage
from inbox.services import (
    ContactMessageEmailService,
    ContactSubmissionService,
    DuplicateSubmission,
    PayloadTooLarge,
)


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


@pytest.mark.django_db
class TestContactSubmissionService:
    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def valid_data(self):
        return {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Hello",
            "message": "This is a test message.",
        }

    def get_drf_request(self, factory, url, data, method="post", content_length=None):
        request = getattr(factory, method)(url, data, format="json")
        if content_length:
            request.META["CONTENT_LENGTH"] = content_length
        return Request(request, parsers=[JSONParser()])

    @patch("inbox.services.ContactMessageEmailService.send_notification_email_async")
    def test_process_submission_success(self, mock_email, factory, valid_data):
        """Test successful service processing"""
        drf_request = self.get_drf_request(factory, "/contact/", valid_data)

        message = ContactSubmissionService.process_submission(drf_request, "127.0.0.1")

        assert isinstance(message, ContactMessage)
        assert message.email == valid_data["email"]
        assert message.subject == valid_data["subject"]
        mock_email.assert_called_once_with(message)

    @patch("inbox.services.logger")
    def test_process_submission_payload_too_large(self, mock_logger, factory, valid_data):
        """Test payload size enforcement"""
        drf_request = self.get_drf_request(factory, "/contact/", valid_data, content_length="10001")

        with pytest.raises(PayloadTooLarge):
            ContactSubmissionService.process_submission(drf_request, "127.0.0.1")

        mock_logger.warning.assert_called()

    @patch("inbox.services.ContactMessageEmailService.send_notification_email_async")
    def test_process_submission_malformed_content_length(self, mock_email, factory, valid_data):
        """Test that malformed content length is ignored"""
        drf_request = self.get_drf_request(factory, "/contact/", valid_data)
        drf_request.META = MagicMock()
        drf_request.META.get.return_value = "not-a-number"

        # Should NOT raise PayloadTooLarge, should proceed normally
        message = ContactSubmissionService.process_submission(drf_request, "127.0.0.1")
        assert isinstance(message, ContactMessage)

    @patch("inbox.services.logger")
    def test_process_submission_invalid_data(self, mock_logger, factory):
        """Test error logging for invalid data"""
        invalid_data = {"email": "invalid"}
        drf_request = self.get_drf_request(factory, "/contact/", invalid_data)

        with pytest.raises(Exception):  # DRF ValidationError
            ContactSubmissionService.process_submission(drf_request, "127.0.0.1")

        mock_logger.error.assert_called()

    @patch("inbox.services.logger")
    def test_process_submission_duplicate(self, mock_logger, factory, valid_data):
        """Test duplicate submission blocking within 5 mins"""
        # Create initial message
        ContactMessage.objects.create(**valid_data)

        drf_request = self.get_drf_request(factory, "/contact/", valid_data)

        with pytest.raises(DuplicateSubmission):
            ContactSubmissionService.process_submission(drf_request, "127.0.0.1")

        msg = f"Duplicate message from {valid_data['email']} w/ subject '{valid_data['subject']}'"
        mock_logger.warning.assert_called_with(f"{msg} at IP 127.0.0.1")

    @patch("inbox.services.logger")
    def test_log_incoming_data_masking(self, mock_logger, factory):
        """Test log masking for emails and long messages"""
        data = {
            "email": "test@example.com",
            "message": "A" * 11,
            "subject": "Short",
            "long_field": "X" * 101,
        }
        drf_request = self.get_drf_request(factory, "/contact/", data)

        ContactSubmissionService.log_incoming_data(drf_request, "127.0.0.1")

        # Check masked data in log call
        args, _ = mock_logger.info.call_args
        log_str = args[0]
        assert "te***@example.com" in log_str
        assert "<11 chars>" in log_str
        assert "X" * 100 + "..." in log_str

    @patch("inbox.services.logger")
    def test_log_incoming_data_malformed_email(self, mock_logger, factory):
        """Test log masking for malformed email strings"""
        data = {"email": "not-an-email"}
        drf_request = self.get_drf_request(factory, "/contact/", data)

        ContactSubmissionService.log_incoming_data(drf_request, "127.0.0.1")

        args, _ = mock_logger.info.call_args
        assert "***" in args[0]
