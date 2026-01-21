import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)


@pytest.mark.django_db
class TestTravelHighlightsBySlugView:
    def setup_method(self):
        self.client = APIClient()
        self.place = PlaceFactory(name="High Tatras")
        self.slider_with_place = MainPageLocationFactory(
            country="PL", place=self.place, is_active=True
        )
        # Ensure slugs are generated
        # (factory might not call save properly if using build, but create calls save)
        # Let's double check slugs are there
        self.slider_with_place.refresh_from_db()

        self.slider_no_place = MainPageLocationFactory(country="US", place=None, is_active=True)
        self.slider_no_place.refresh_from_db()

        # Create some images
        self.img1 = AstroImageFactory(location="PL", place=self.place, name="Tatras 1")
        self.img2 = AstroImageFactory(
            location="PL", place=None, name="Poland 1"
        )  # Should not be in place slider
        self.img3 = AstroImageFactory(location="US", place=None, name="USA 1")

    def test_get_by_country_slug(self):
        url = reverse("astroimages:travel-by-country", args=[self.slider_no_place.country_slug])
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["country"] == "United States of America"
        assert data["place"] is None
        assert len(data["images"]) == 1
        assert "United States" in data["images"][0]["location"]

    def test_get_by_country_and_place_slug(self):
        url = reverse(
            "astroimages:travel-by-country-place",
            args=[self.slider_with_place.country_slug, self.slider_with_place.place_slug],
        )
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["country"] == "Poland"
        assert data["place"] == "High Tatras"
        assert len(data["images"]) == 1
        assert data["images"][0]["name"] == "Tatras 1"

    def test_get_invalid_slug_returns_404(self):
        url = reverse("astroimages:travel-by-country", args=["invalid-slug"])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_slider_returns_404(self):
        self.slider_no_place.is_active = False
        self.slider_no_place.save()

        url = reverse("astroimages:travel-by-country", args=[self.slider_no_place.country_slug])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
