import pytest
from rest_framework import status

from django.urls import reverse

from astrophotography.models import MeteorsMainPageConfig
from astrophotography.tests.factories import MeteorsMainPageConfigFactory
from core.tests.factories import LandingPageSettingsFactory


@pytest.mark.django_db
class TestSettingsView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("settings")

    def test_whats_enabled_all_disabled(self, api_client):
        """Test that the endpoint returns an empty dictionary when all features are disabled"""
        LandingPageSettingsFactory(
            programming_enabled=False,
            contact_form_enabled=False,
            travel_highlights_enabled=False,
            lastimages_enabled=False,
            meteors=None,
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["programming"] is False
        assert response.data["contactForm"] is False
        assert response.data["travelHighlights"] is False
        assert response.data["lastimages"] is False
        assert response.data["meteors"] is None

    def test_whats_enabled_programming_only(self, api_client):
        """Test that only 'programming' is returned when it's enabled"""
        LandingPageSettingsFactory(
            programming_enabled=True,
            contact_form_enabled=False,
            travel_highlights_enabled=False,
            lastimages_enabled=False,
            meteors=None,
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["programming"] is True
        assert response.data["contactForm"] is False
        assert response.data["travelHighlights"] is False
        assert response.data["lastimages"] is False
        assert response.data["meteors"] is None

    def test_whats_enabled_contact_form_only(self, api_client):
        """Test that only 'contactForm' is returned when it's enabled"""
        LandingPageSettingsFactory(
            programming_enabled=False,
            contact_form_enabled=True,
            travel_highlights_enabled=False,
            lastimages_enabled=False,
            meteors=None,
        )
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["programming"] is False
        assert response.data["contactForm"] is True
        assert response.data["travelHighlights"] is False
        assert response.data["lastimages"] is False
        assert response.data["meteors"] is None

    def test_whats_enabled_all_enabled(self, api_client):
        """Test that all features are returned when they are enabled"""
        MeteorsMainPageConfig.objects.all().delete()
        meteor_config = MeteorsMainPageConfigFactory()
        LandingPageSettingsFactory(
            programming_enabled=True,
            contact_form_enabled=True,
            travel_highlights_enabled=True,
            meteors=meteor_config,
        )

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["programming"] is True
        assert response.data["contactForm"] is True
        assert response.data["travelHighlights"] is True
        assert response.data["lastimages"] is True
        assert response.data["meteors"]["randomShootingStars"] is True
        assert response.data["meteors"]["bolidChance"] == meteor_config.bolid_chance
