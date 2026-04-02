# backend/inbox/tests/test_services.py
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from inbox.models import ContactMessage
from inbox.services import ContactSubmissionService, DuplicateSubmission
from inbox.tasks import EmailHandler
from inbox.tests.factories import ContactMessageFactory
from users.models import Profile
from users.tests.factories import ProfileFactory, UserFactory


@pytest.mark.django_db
class TestEmailHandler:
    def test_send_email_success(
        self,
        mock_inbox_email_message: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test successful email sending"""
        with override_settings(SIMULATE_CONTACT_EMAILS=False):
            user = UserFactory(first_name="Lukasz", last_name="Remkowicz")
            ProfileFactory(
                user=user,
                type=Profile.ProfileType.ASTRO,
                ig_url="https://instagram.com/test",
                fb_url="https://facebook.com/test",
                astrobin_url="https://astrobin.com/test",
            )

            # Call the service method
            EmailHandler.send_email(contact_message)

            assert mock_inbox_email_message.call_count == 2

            owner_call = mock_inbox_email_message.call_args_list[0]
            _, owner_kwargs = owner_call
            assert owner_kwargs["subject"] == f"New Contact Message: {contact_message.subject}"
            assert owner_kwargs["to"] == [settings.CONTACT_EMAIL]
            assert contact_message.message in owner_kwargs["body"]
            assert contact_message.email in owner_kwargs["body"]

            sender_call = mock_inbox_email_message.call_args_list[1]
            _, email_kwargs = sender_call
            assert email_kwargs["subject"] == "Message Received - Astrophotography Portfolio"
            assert email_kwargs["to"] == [contact_message.email]
            assert email_kwargs["reply_to"] == [settings.CONTACT_EMAIL]
            assert "Message Received" in email_kwargs["body"]
            assert "https://portfolio.local/astrophotography" in email_kwargs["body"]
            assert "https://instagram.com/test" in email_kwargs["body"]
            assert "https://facebook.com/test" in email_kwargs["body"]
            assert "https://astrobin.com/test" in email_kwargs["body"]
            assert f"\u00a9 {timezone.now().year} owner" in email_kwargs["body"]
            assert "Thank you for reaching out" in email_kwargs["body"]
            assert mock_inbox_email_message.return_value.send.call_count == 2
            mock_inbox_email_message.return_value.send.assert_called_with(fail_silently=False)
            # Verify logger info was called
            mock_inbox_logger.info.assert_any_call(
                "Owner notification email sent for message ID=%s to %s",
                contact_message.id,
                settings.CONTACT_EMAIL,
            )
            mock_inbox_logger.info.assert_any_call(
                "Sender confirmation email sent for message ID=%s to %s",
                contact_message.id,
                contact_message.email,
            )
            mock_inbox_logger.info.assert_any_call(
                f"Email notifications sent for message ID={contact_message.id}"
            )

    def test_send_notification_email_simulation(
        self,
        mock_inbox_email_message: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test that email is simulated when SIMULATE_CONTACT_EMAILS=True."""

        with override_settings(DEBUG=False, SIMULATE_CONTACT_EMAILS=True):
            # Call the handler method
            EmailHandler.send_email(contact_message)

        mock_inbox_email_message.assert_not_called()

        # Verify logger.info was called with simulation messages
        mock_inbox_logger.info.assert_any_call(
            "SIMULATE_CONTACT_EMAILS=True: Simulating contact email send."
        )
        mock_inbox_logger.info.assert_any_call(
            f"Fake Email notifications sent for message ID={contact_message.id}"
        )

    def test_send_email_failure(
        self,
        mock_inbox_email_message: MagicMock,
        mock_inbox_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Test failure handling when send_mail raises exception"""
        with override_settings(SIMULATE_CONTACT_EMAILS=False):
            # Simulate EmailMessage.send raising an exception
            mock_inbox_email_message.return_value.send.side_effect = Exception("SMTP Error")

            # Call the service method
            EmailHandler.send_email(contact_message)

            # Verify error was logged
            mock_inbox_logger.error.assert_called_with(
                f"Failed to send email notifications for message ID={contact_message.id}: "
                f"SMTP Error"
            )


@pytest.mark.django_db
class TestContactSubmissionService:

    def test_check_duplicate_success(self, valid_contact_data: dict[str, str]) -> None:
        """Test that check_duplicate proceeds normally when no duplicate exists"""
        # Should not raise any exception
        ContactSubmissionService.check_duplicate(valid_contact_data, "127.0.0.1")

    def test_check_duplicate_raises_exception(
        self,
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
        mock_enqueue = mocker.patch("inbox.services.ContactSubmissionService._enqueue_email_task")

        ContactSubmissionService.finalize_submission(contact_message, "127.0.0.1")
        mock_enqueue.assert_called_once_with(contact_message.id)

    def test_enqueue_email_task_broker_failure_does_not_raise(
        self,
        mocker: MockerFixture,
        mock_inbox_service_logger: MagicMock,
        contact_message: ContactMessage,
    ) -> None:
        """Broker failures should be logged without raising."""
        mock_apply_async = mocker.patch("inbox.services.send_notification_email_task.apply_async")
        mock_apply_async.side_effect = Exception("Broker unavailable")

        ContactSubmissionService._enqueue_email_task(contact_message.id)

        mock_inbox_service_logger.warning.assert_called_once()
        args, _ = mock_inbox_service_logger.warning.call_args
        assert args[0] == "Failed to enqueue contact email task for message ID=%s: %s"
        assert args[1] == contact_message.id
        assert str(args[2]) == "Broker unavailable"

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
