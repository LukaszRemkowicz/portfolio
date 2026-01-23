# backend/inbox/tests/test_models.py
import pytest

from inbox.tests.factories import ContactMessageFactory


@pytest.mark.django_db
class TestInboxModels:
    def test_contact_message_str(self):
        """Verify ContactMessage string representation"""
        contact_message = ContactMessageFactory()
        expected_str = (
            f"{contact_message.name} - {contact_message.subject} "
            f"({contact_message.created_at.strftime('%Y-%m-%d %H:%M')})"
        )
        assert str(contact_message) == expected_str
