from unittest.mock import patch

import pytest

from django.db import IntegrityError

from inbox.models import ContactFormSettings, ContactMessage


@pytest.mark.django_db
class TestInboxModels:
    def test_contact_message_str(self):
        """Verify ContactMessage string representation"""
        message = ContactMessage.objects.create(
            name="Alice", email="alice@example.com", subject="Question", message="Hi there"
        )
        expected_str = f"Alice - Question ({message.created_at.strftime('%Y-%m-%d %H:%M')})"
        assert str(message) == expected_str

    def test_contact_form_settings_str(self):
        """Verify ContactFormSettings string representation"""
        settings = ContactFormSettings.get_settings()
        settings.enabled = True
        assert str(settings) == "Contact Form Settings (Enabled: True)"

    def test_contact_form_settings_singleton_get_settings(self):
        """Verify get_settings returns singleton and creates it if missing"""
        ContactFormSettings.objects.all().delete()

        settings = ContactFormSettings.get_settings()
        assert settings.pk == 1
        assert settings.enabled is False

        # Call again
        settings_again = ContactFormSettings.get_settings()
        assert settings_again.pk == settings.pk

    def test_contact_form_settings_save_enforces_pk1(self):
        """Verify that save() always sets pk=1"""
        settings = ContactFormSettings(enabled=True)
        settings.save()
        assert settings.pk == 1

        # Try to save another instance with different PK
        settings_other = ContactFormSettings(pk=2, enabled=False)
        settings_other.save()
        assert settings_other.pk == 1

        assert ContactFormSettings.objects.count() == 1

    def test_contact_form_settings_save_integrity_error_handling(self):
        """Verify handling of IntegrityError during save (race condition)"""
        # Create initial real record
        ContactFormSettings.objects.create(pk=1, enabled=False)

        # Now mock the super().save to raise IntegrityError
        with patch("django.db.models.Model.save") as mock_super_save:
            mock_super_save.side_effect = IntegrityError("Unique constraint")

            settings = ContactFormSettings(pk=1, enabled=True)
            # Should catch IntegrityError and call update()
            settings.save()

        # Verify the update actually happened via the update() path
        final_settings = ContactFormSettings.objects.get(pk=1)
        assert final_settings.enabled is True

    @patch("django.db.models.Model.save")
    @patch("inbox.models.logger")
    def test_contact_form_settings_save_unexpected_error(self, mock_logger, mock_super_save):
        """Verify logging of unexpected errors during save"""
        mock_super_save.side_effect = Exception("Boom")

        settings = ContactFormSettings(pk=1)
        with pytest.raises(Exception, match="Boom"):
            settings.save()

        mock_logger.error.assert_called()
