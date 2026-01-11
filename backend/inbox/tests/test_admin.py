from unittest.mock import MagicMock

import pytest

from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from inbox.admin import ContactFormSettingsAdmin, ContactMessageAdmin
from inbox.models import ContactFormSettings, ContactMessage


@pytest.mark.django_db
class TestContactMessageAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = ContactMessageAdmin(ContactMessage, self.site)
        self.message = ContactMessage.objects.create(
            name="Test", email="test@example.com", subject="Sub", message="Msg"
        )

    def test_changeform_view_marks_as_read(self, rf):
        """Verify that viewing a message in admin marks it as read"""
        assert self.message.is_read is False

        request = rf.get(reverse("admin:inbox_contactmessage_change", args=[self.message.pk]))
        request.user = MagicMock()
        request.session = MagicMock()
        # Mocking _messages for admin views that might use messages framework
        request._messages = MagicMock()

        # Call changeform_view
        self.admin.changeform_view(request, object_id=str(self.message.pk))

        self.message.refresh_from_db()
        assert self.message.is_read is True

    def test_changeform_view_invalid_id(self, rf):
        """Verify that invalid IDs don't cause errors"""
        request = rf.get("/")
        request.user = MagicMock()
        request.session = MagicMock()
        request._messages = MagicMock()
        # Should not raise exception
        self.admin.changeform_view(request, object_id="999")


@pytest.mark.django_db
class TestContactFormSettingsAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = ContactFormSettingsAdmin(ContactFormSettings, self.site)
        ContactFormSettings.objects.all().delete()

    def test_has_add_permission(self):
        """Verify only one instance can be added"""
        request = MagicMock()
        assert self.admin.has_add_permission(request) is True

        ContactFormSettings.objects.create(pk=1)
        assert self.admin.has_add_permission(request) is False

    def test_has_delete_permission(self):
        """Verify deletion is always disabled"""
        assert self.admin.has_delete_permission(MagicMock()) is False

    def test_changelist_view_redirects_to_singleton(self, rf):
        """Verify redirect to the singleton instance if it exists"""
        settings = ContactFormSettings.get_settings()
        request = rf.get(reverse("admin:inbox_contactformsettings_changelist"))
        request.user = MagicMock()

        response = self.admin.changelist_view(request)

        assert response.status_code == 302
        assert response.url == reverse("admin:inbox_contactformsettings_change", args=[settings.pk])
