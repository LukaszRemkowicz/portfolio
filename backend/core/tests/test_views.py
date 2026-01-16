import pytest
from rest_framework import status

from django.urls import reverse

from core.models import LandingPageSettings
from core.tests.factories import LandingPageSettingsFactory


@pytest.mark.django_db
class TestFeaturesEnabledView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("whats-enabled")
        # Clear/initialize singletons
        LandingPageSettings.objects.all().delete()

    def test_whats_enabled_all_disabled(self, api_client):
        """Test that the endpoint returns an empty dictionary when all features are disabled"""
        LandingPageSettingsFactory(
            programming_enabled=False, contact_form_enabled=False, location_slider_enabled=False
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_whats_enabled_programming_only(self, api_client):
        """Test that only 'programming' is returned when it's enabled"""
        LandingPageSettingsFactory(
            programming_enabled=True, contact_form_enabled=False, location_slider_enabled=False
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True}

    def test_whats_enabled_contact_form_only(self, api_client):
        """Test that only 'contactForm' is returned when it's enabled"""
        LandingPageSettingsFactory(
            programming_enabled=False, contact_form_enabled=True, location_slider_enabled=False
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"contactForm": True}

    def test_whats_enabled_all_enabled(self, api_client):
        """Test that all features are returned when they are enabled"""
        LandingPageSettingsFactory(
            programming_enabled=True, contact_form_enabled=True, location_slider_enabled=True
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"programming": True, "contactForm": True, "locationSlider": True}

    def test_whats_enabled_default_values(self, api_client):
        """Test that default values are True if no settings exist"""
        # Ensure no settings record exists
        LandingPageSettings.objects.all().delete()

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        # Defaults in view should be True for all
        assert response.data == {"programming": True, "contactForm": True, "locationSlider": True}
