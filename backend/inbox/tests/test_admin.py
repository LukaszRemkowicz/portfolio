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
        self.site = AdminSite()
        self.admin = ContactMessageAdmin(ContactMessage, self.site)
        self.message = ContactMessageFactory(
            name="Test", email="test@example.com", subject="Sub", message="Msg"
        )

    def test_changeform_view_marks_as_read(self, rf: RequestFactory) -> None:
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

    def test_changeform_view_invalid_id(self, rf: RequestFactory) -> None:
        """Verify that invalid IDs don't cause errors"""
        request = rf.get("/")
        request.user = MagicMock()
        request.session = MagicMock()
        request._messages = MagicMock()
        # Should not raise exception
        self.admin.changeform_view(request, object_id="999")
