# backend/inbox/tests/test_tasks.py
import pytest
from pytest_mock import MockerFixture

from inbox.tasks import send_notification_email_task
from inbox.tests.factories import ContactMessageFactory


@pytest.mark.django_db
def test_send_notification_email_task_success(mocker: MockerFixture):
    """Test that send_notification_email_task calls the email service correctly."""
    # Create a message
    contact_message = ContactMessageFactory()

    # Mock the handler method
    mock_send = mocker.patch("inbox.tasks.EmailHandler.send_email")

    # Call the task
    send_notification_email_task(contact_message.id)

    # Verify the service was called with the correct message
    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    assert args[0].id == contact_message.id


@pytest.mark.django_db
def test_send_notification_email_task_message_not_found(mocker: MockerFixture):
    """Test that task handles non-existent message IDs gracefully."""
    mock_logger = mocker.patch("inbox.tasks.logger")
    mock_send = mocker.patch("inbox.tasks.EmailHandler.send_email")

    # Call with non-existent ID
    send_notification_email_task(9999)

    # Verify send was NOT called
    mock_send.assert_not_called()

    # Verify error was logged
    mock_logger.error.assert_called_once()
    assert "Message 9999 not found" in mock_logger.error.call_args[0][0]
