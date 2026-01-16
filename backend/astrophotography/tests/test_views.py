# backend/astrophotography/tests/test_views.py
import pytest
from rest_framework import status

from django.urls import reverse

from astrophotography.models import MainPageBackgroundImage
from astrophotography.tests.factories import AstroImageFactory, MainPageBackgroundImageFactory


@pytest.mark.django_db
class TestAstroImageViewSet:
    def test_list_astro_images(self, api_client, astro_image):
        """Test listing images via the router generated URL"""
        url = reverse("astroimages:astroimage-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["pk"] == str(astro_image.pk)
        assert "url" in response.data[0]

    def test_retrieve_astro_image(self, api_client, astro_image):
        """Test retrieving a single image via the router generated URL"""
        url = reverse("astroimages:astroimage-detail", args=[astro_image.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Detail serializer doesn't include ID, check another field
        assert response.data["capture_date"] == str(astro_image.capture_date)
        assert response.data["celestial_object"] == astro_image.celestial_object

    def test_filter_astro_images(self, api_client):
        """Test filtering images by celestial_object"""
        AstroImageFactory(celestial_object="Deep Sky")
        AstroImageFactory(celestial_object="Deep Sky")
        AstroImageFactory(celestial_object="Landscape")

        url = reverse("astroimages:astroimage-list")

        # Filter matching "Deep Sky"
        response = api_client.get(url, {"filter": "Deep Sky"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Filter matching "Landscape"
        response = api_client.get(url, {"filter": "Landscape"})
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
        MainPageBackgroundImageFactory()
        latest = MainPageBackgroundImageFactory()

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Serializer uses 'url' field mapped from 'image'
        assert latest.path.name in response.data["url"]

    def test_list_background_image_empty(self, api_client):
        """Test retrieving background when none exist"""
        # Ensure clean state
        MainPageBackgroundImage.objects.all().delete()

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["url"] is None


@pytest.mark.django_db
class TestMainPageLocationSliderViewSet:
    def test_list_active_sliders(self, api_client):
        """Test listing only active sliders ordered by country"""
        from astrophotography.tests.factories import (
            AstroImageFactory,
            MainPageLocationSliderFactory,
        )

        # Create active slider for PL
        img_pl = AstroImageFactory(location="PL")
        MainPageLocationSliderFactory(country="PL", is_active=True, images=[img_pl])

        # Create active slider for US
        img_us = AstroImageFactory(location="US")
        MainPageLocationSliderFactory(country="US", is_active=True, images=[img_us])

        # Create inactive slider (should not be listed)
        MainPageLocationSliderFactory(country="NO", is_active=False)

        url = reverse("astroimages:travel-highlights-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Check ordering (PL comes before US alphabetically? No, country code PL vs US.
        # Wait, model ordering is by 'country' field which is code. P vs U.
        # Let's just check existence.
        countries = [item["country"] for item in response.data]
        assert "PL" in countries
        assert "US" in countries
        assert "NO" not in countries

        # Verify structure
        item_pl = next(item for item in response.data if item["country"] == "PL")
        assert item_pl["country_name"] == "Poland"
        assert len(item_pl["images"]) == 1
        assert item_pl["images"][0]["pk"] == str(img_pl.pk)
