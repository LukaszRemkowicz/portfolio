from unittest.mock import MagicMock

import pytest

from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from programming.admin import ProgrammingPageConfigAdmin
from programming.models import ProgrammingPageConfig


@pytest.mark.django_db
class TestProgrammingPageConfigAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = ProgrammingPageConfigAdmin(ProgrammingPageConfig, self.site)
        ProgrammingPageConfig.objects.all().delete()

    def test_has_add_permission(self):
        """Verify only one config instance can be added"""
        request = MagicMock()
        assert self.admin.has_add_permission(request) is True

        ProgrammingPageConfig.objects.create(pk=1)
        assert self.admin.has_add_permission(request) is False

    def test_has_delete_permission(self):
        """Verify deletion of config is disabled"""
        assert self.admin.has_delete_permission(MagicMock()) is False

    def test_changelist_view_redirects_to_singleton(self, rf):
        """Verify redirect to the change view if config exists"""
        config = ProgrammingPageConfig.get_config()
        # Ensure it has a PK (get_config should ensure this but good to be explicit)
        assert config.pk is not None

        request = rf.get(reverse("admin:programming_programmingpageconfig_changelist"))

        response = self.admin.changelist_view(request)

        assert response.status_code == 302
        # Use dynamic model name resolution if needed, but here we know it
        expected_url = reverse("admin:programming_programmingpageconfig_change", args=[config.pk])
        assert response.url == expected_url
