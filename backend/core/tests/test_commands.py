import pytest
from rest_framework import status

from django.core.management import call_command
from django.urls import reverse

from astrophotography.models import MeteorsMainPageConfig
from core.models import LandingPageSettings


@pytest.mark.django_db
class TestSeedSettingsCommand:
    def test_seed_settings_creates_defaults(self, api_client):
        """Test that seed_settings command creates default settings and config"""
        # Ensure no settings record exists
        LandingPageSettings.objects.all().delete()
        MeteorsMainPageConfig.objects.all().delete()

        # Run seeding
        call_command("seed_settings")

        # Verify through the settings API (integrative test)
        url = reverse("settings")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Defaults should be True, and meteors should be auto-linked
        assert response.data["programming"] is True
        assert response.data["contactForm"] is True
        assert response.data["travelHighlights"] is True
        assert response.data["lastimages"] is True
        assert response.data["meteors"]["randomShootingStars"] is True
