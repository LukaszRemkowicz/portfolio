import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory, PlaceFactory


@pytest.mark.django_db
class TestAstroImageViewSetCountryPlaceFiltering:
    """
    Test country and place filtering for AstroImageViewSet.
    """

    def setup_method(self):
        """Create test client and baseline data."""
        self.client = APIClient()
        self.url = reverse("astroimages:astroimage-list")

        # Create test images with different locations
        self.us_image1 = AstroImageFactory(location="US", place=None, name="US Image 1")
        self.us_image2 = AstroImageFactory(location="US", place=None, name="US Image 2")
        self.pl_image1 = AstroImageFactory(location="PL", place=None, name="PL Image 1")

        # Create place for more specific filtering
        self.hawaii_place = PlaceFactory(name="Hawaii")
        self.us_hawaii_image = AstroImageFactory(
            location="US", place=self.hawaii_place, name="US Hawaii Image"
        )

    def test_filter_by_country_code(self):
        """Test filtering images by country code."""
        response = self.client.get(self.url, {"country": "US"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # us_image1, us_image2, us_hawaii_image
        assert all(img["location"] == "US" for img in data)

    def test_filter_by_invalid_country_code(self):
        """Test filtering by non-existent country code returns empty list."""
        response = self.client.get(self.url, {"country": "XX"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_filter_by_country_and_place(self):
        """Test filtering by both country and place."""
        response = self.client.get(self.url, {"country": "US", "place": "Hawaii"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should include us_hawaii_image and images with NULL place
        assert len(data) == 3  # us_image1, us_image2, us_hawaii_image
        assert all(img["location"] == "US" for img in data)

    def test_filter_by_country_and_non_existent_place(self):
        """Test filtering by country and non-existent place includes NULL place images."""
        response = self.client.get(self.url, {"country": "US", "place": "Alaska"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should include only images with NULL place (us_image1, us_image2)
        assert len(data) == 2
        assert all(img["location"] == "US" for img in data)

    def test_place_filter_without_country_ignored(self):
        """Test that place filter alone is ignored (requires country)."""
        # Create more images to ensure we get all images
        AstroImageFactory(location="NO", place=None)

        response = self.client.get(self.url, {"place": "Hawaii"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return all images since place filter requires country
        assert len(data) == 5  # All images created in setup + NO image

    def test_travel_param_fuzzy_country_matching(self):
        """Test fuzzy country matching with travel parameter."""
        response = self.client.get(self.url, {"travel": "Poland"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should match Poland images
        assert len(data) >= 1
        assert any(img["location"] == "PL" for img in data)

    def test_no_filters_returns_all_images(self):
        """Test that no filters return all images."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4  # All images from setup
