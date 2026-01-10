# backend/users/tests/test_admin.py
from unittest.mock import patch

import pytest

from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from users.admin import UserAdmin, UserLoginAttemptsAdmin
from users.models import User, UserLoginAttempts


class MockRequest:
    def __init__(self, user=None):
        self.user = user


@pytest.mark.django_db
class TestUserAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)

    def test_has_add_permission_no_user(self):
        """Should have add permission if no user exists"""
        assert User.objects.count() == 0
        assert self.admin.has_add_permission(MockRequest()) is True

    def test_has_add_permission_with_user(self):
        """Should NOT have add permission if a user already exists"""
        User.objects.create(email="test@example.com")
        assert User.objects.count() == 1
        assert self.admin.has_add_permission(MockRequest()) is False

    def test_has_delete_permission(self):
        """Should never have delete permission"""
        assert self.admin.has_delete_permission(MockRequest()) is False

    def test_changelist_view_no_user(self):
        """Should return result of super().changelist_view if no user exists"""
        assert User.objects.count() == 0
        request = MockRequest()

        # We can't easily mock super, but we can call it and verify it returns a response
        # instead of a redirect.
        # This will cover line 95 in admin.py.
        with patch("django.contrib.admin.options.ModelAdmin.changelist_view") as mock_super_view:
            mock_super_view.return_value = "super result"
            response = self.admin.changelist_view(request)
            assert response == "super result"

    def test_changelist_view_redirects_if_user_exists(self):
        """Should redirect to change view if user exists"""
        user = User.objects.create(email="test@example.com")
        request = MockRequest()

        response = self.admin.changelist_view(request)

        expected_url = reverse("admin:users_user_change", args=[user.pk])
        assert response.status_code == 302
        assert response.url == expected_url


@pytest.mark.django_db
class TestUserLoginAttemptsAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = UserLoginAttemptsAdmin(UserLoginAttempts, self.site)

    def test_admin_setup(self):
        """Verify admin config"""
        assert "attempted_at" in self.admin.list_display
        assert "counter" in self.admin.list_display
