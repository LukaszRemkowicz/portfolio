# backend/inbox/tests/test_admin.py
from unittest.mock import MagicMock

import pytest

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from inbox.admin import ContactMessageAdmin
from inbox.models import ContactMessage
from inbox.tests.factories import ContactMessageFactory


@pytest.mark.django_db
class TestContactMessageAdmin:
    def setup_method(self) -> None:
        self.admin_site = AdminSite()
        self.message_admin = ContactMessageAdmin(ContactMessage, self.admin_site)
        self.contact_message = ContactMessageFactory(
            name="Test", email="test@example.com", subject="Sub", message="Msg"
        )

    def test_changeform_view_marks_as_read(self, request_factory: RequestFactory) -> None:
        """Verify that viewing a message in admin marks it as read"""
        assert self.contact_message.is_read is False

        request_url = reverse("admin:inbox_contactmessage_change", args=[self.contact_message.pk])
        request = request_factory.get(request_url)
        request.user = MagicMock()
        request.session = MagicMock()
        # Mocking _messages for admin views that might use messages framework
        request._messages = MagicMock()

        # Call changeform_view
        self.message_admin.changeform_view(request, object_id=str(self.contact_message.pk))

        self.contact_message.refresh_from_db()
        assert self.contact_message.is_read is True

    def test_changeform_view_invalid_id(self, request_factory: RequestFactory) -> None:
        """Verify that invalid IDs don't cause errors"""
        request = request_factory.get("/")
        request.user = MagicMock()
        request.session = MagicMock()
        request._messages = MagicMock()
        # Should not raise exception
        self.message_admin.changeform_view(request, object_id="999")
