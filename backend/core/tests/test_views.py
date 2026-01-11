import pytest
from rest_framework import status

from django.urls import reverse

from inbox.models import ContactFormSettings
from programming.models import ProgrammingPageConfig


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
        ProgrammingPageConfig.get_config()
        ContactFormSettings.get_settings()

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_whats_enabled_programming_only(self, api_client):
        """Test that only 'programming' is returned when it's enabled"""
        config = ProgrammingPageConfig.get_config()
        config.enabled = True
        config.save()

        # Contact form disabled by default
        ContactFormSettings.get_settings()

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True}

    def test_whats_enabled_contact_form_only(self, api_client):
        """Test that only 'contactForm' is returned when it's enabled"""
        settings = ContactFormSettings.get_settings()
        settings.enabled = True
        settings.save()

        # Programming disabled by default
        ProgrammingPageConfig.get_config()

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"contactForm": True}

    def test_whats_enabled_all_enabled(self, api_client):
        """Test that both features are returned when they are both enabled"""
        config = ProgrammingPageConfig.get_config()
        config.enabled = True
        config.save()

        settings = ContactFormSettings.get_settings()
        settings.enabled = True
        settings.save()

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True, "contactForm": True}
