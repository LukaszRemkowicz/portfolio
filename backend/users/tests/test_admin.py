# backend/users/tests/test_admin.py

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from pytest_mock import MockerFixture

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.urls import reverse

from users.admin import UserAdmin
from users.tests.factories import UserFactory

User = get_user_model()


class MockRequest:
    def __init__(self, user=None):
        self.user = user
        self.GET = QueryDict("", mutable=True)


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
        UserFactory()
        assert User.objects.count() == 1
        assert self.admin.has_add_permission(MockRequest()) is False

    def test_has_delete_permission(self):
        """Should never have delete permission"""
        assert self.admin.has_delete_permission(MockRequest()) is False

    def test_changelist_view_no_user(self, mocker: MockerFixture):
        """Should return result of super().changelist_view if no user exists"""
        assert User.objects.count() == 0
        request = MockRequest()

        # We can't easily mock super, but we can call it and verify it returns a response
        # instead of a redirect.
        # This will cover line 95 in admin.py.
        mock_super_view = mocker.patch("django.contrib.admin.options.ModelAdmin.changelist_view")
        mock_super_view.return_value = "super result"
        response = self.admin.changelist_view(request)
        assert response == "super result"

    def test_changelist_view_redirects_if_user_exists(self):
        """Should redirect to change view if user exists"""
        user = UserFactory()
        request = MockRequest()

        response = self.admin.changelist_view(request)

        expected_url = reverse("admin:users_user_change", args=[user.pk])
        assert response.status_code == 302
        assert response.url == expected_url

    def test_change_view_adds_avatar_cropper_context(self, mocker: MockerFixture):
        user = UserFactory.create_superuser()
        request = MockRequest(user=user)
        request.GET = QueryDict("", mutable=True)

        captured = {}

        def fake_change_view(self, request, object_id, form_url="", extra_context=None):
            captured["extra_context"] = extra_context
            return "ok"

        mocker.patch.object(
            UserAdmin.__mro__[5],
            "change_view",
            fake_change_view,
        )

        response = self.admin.change_view(request, str(user.pk))

        assert response == "ok"
        assert captured["extra_context"]["admin_image_cropper"]["field_name"] == "avatar"
        assert captured["extra_context"]["admin_image_cropper"]["visible_tab_panel"] == "media-tab"


@pytest.mark.django_db
def test_change_form_mounts_cropper_component_in_sidebar(client):
    user = UserFactory.create_superuser()
    client.force_login(user)

    url = reverse("admin:users_user_change", args=[user.pk])
    response = client.get(url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    jazzy_actions = soup.select_one("#jazzy-actions")
    assert jazzy_actions is not None

    object_tools = jazzy_actions.select_one(".object-tools")
    cropper_root = jazzy_actions.select_one("[data-admin-image-cropper-root]")

    assert object_tools is not None
    assert cropper_root is not None
    assert cropper_root["data-field-name"] == "avatar"
    assert cropper_root["data-visible-tab-panel"] == "media-tab"

    object_tools_index = str(jazzy_actions).index("object-tools")
    cropper_index = str(jazzy_actions).index("data-admin-image-cropper-root")
    assert object_tools_index < cropper_index


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "pl"])
def test_change_form_renders_cropper_component_for_each_language_tab(client, language):
    user = UserFactory.create_superuser()
    client.force_login(user)

    url = reverse("admin:users_user_change", args=[user.pk])
    response = client.get(f"{url}?language={language}")

    assert response.status_code == 200
    content = response.content.decode()
    assert "data-admin-image-cropper-root" in content
    assert 'data-visible-tab-panel="media-tab"' in content
    assert "/static/users/js/admin_image_cropper.js" in content


def test_change_form_template_uses_jazzmin_wrapper():
    """The custom user change form should stay on the Jazzmin admin path."""
    template_path = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "admin"
        / "users"
        / "user"
        / "robust_change_form.html"
    )

    template_source = template_path.read_text()

    assert '{% extends "admin/change_form.html" %}' in template_source
