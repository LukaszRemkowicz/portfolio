import pytest
from rest_framework import status

from django.urls import reverse

from inbox.models import ContactFormSettings
from inbox.tests.factories import ContactFormSettingsFactory
from programming.models import ProgrammingPageConfig
from programming.tests.factories import ProgrammingPageConfigFactory


@pytest.mark.django_db
@pytest.mark.django_db
class TestFeaturesEnabledView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("whats-enabled")

        # Clear/initialize singletons
        ProgrammingPageConfig.objects.all().delete()
        ContactFormSettings.objects.all().delete()

    def test_whats_enabled_all_disabled(self, api_client):
        """Test that the endpoint returns an empty dictionary when all features are disabled"""
        # Ensure singletons exist and are disabled (default)
        ProgrammingPageConfigFactory(enabled=False)
        ContactFormSettingsFactory(enabled=False)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_whats_enabled_programming_only(self, api_client):
        """Test that only 'programming' is returned when it's enabled"""
        ProgrammingPageConfigFactory(enabled=True)

        # Contact form disabled by default
        ContactFormSettingsFactory(enabled=False)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True}

    def test_whats_enabled_contact_form_only(self, api_client):
        """Test that only 'contactForm' is returned when it's enabled"""
        ContactFormSettingsFactory(enabled=True)

        # Programming disabled by default
        ProgrammingPageConfigFactory(enabled=False)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"contactForm": True}

    def test_whats_enabled_all_enabled(self, api_client):
        """Test that both features are returned when they are both enabled"""
        ProgrammingPageConfigFactory(enabled=True)
        ContactFormSettingsFactory(enabled=True)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True, "contactForm": True}
