# backend/astrophotography/tests/test_views.py
import pytest
from rest_framework import status

from django.urls import reverse

from astrophotography.models import BackgroundMainPage


@pytest.mark.django_db
class TestAstroImageViewSet:
    def test_list_astro_images(self, api_client, astro_image):
        """Test listing images via the router generated URL"""
        url = reverse("astroimages:astroimage-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["pk"] == str(astro_image.pk)

    def test_retrieve_astro_image(self, api_client, astro_image):
        """Test retrieving a single image via the router generated URL"""
        url = reverse("astroimages:astroimage-detail", args=[astro_image.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Detail serializer doesn't include ID, check another field
        assert response.data["capture_date"] == str(astro_image.capture_date)

    def test_filter_astro_images(self, api_client, astro_image):
        """Test filtering images by celestial_object"""
        url = reverse("astroimages:astroimage-list")
        # Filter matching
        response = api_client.get(url, {"filter": "Deep Sky"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        # Filter not matching
        response = api_client.get(url, {"filter": "Planetary"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


@pytest.mark.django_db
class TestBackgroundMainPageView:
    def test_list_background_image(self, api_client):
        """Test retrieving the latest background image"""
        # Create two images, should retrieve the latest one
        BackgroundMainPage.objects.create(image="old.jpg")
        BackgroundMainPage.objects.create(image="new.jpg")

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Serializer uses 'url' field mapped from 'image'
        # Note: testing full URL requires request context which we have
        assert "new.jpg" in response.data["url"]

    def test_list_background_image_empty(self, api_client):
        """Test retrieving background when none exist"""
        # Ensure clean state
        BackgroundMainPage.objects.all().delete()

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["url"] is None
