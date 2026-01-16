import pytest

from inbox.tests.factories import ContactMessageFactory


@pytest.mark.django_db
class TestInboxModels:
    def test_contact_message_str(self):
        """Verify ContactMessage string representation"""
        message = ContactMessageFactory()
        expected_str = (
            f"{message.name} - {message.subject} ({message.created_at.strftime('%Y-%m-%d %H:%M')})"
        )
        assert str(message) == expected_str
