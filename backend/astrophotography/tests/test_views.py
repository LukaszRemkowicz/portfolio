# backend/astrophotography/tests/test_views.py
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.models import AstroImage, CelestialObjectChoices, MainPageBackgroundImage
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
    TagFactory,
)
from common.utils.signing import generate_signed_url_params


@pytest.mark.django_db
class TestAstroImageViewSet:
    def test_list_astro_images(self, api_client: APIClient, astro_image: AstroImage) -> None:
        """Test listing images via the router generated URL"""
        url = reverse("astroimages:astroimage-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["pk"] == str(astro_image.pk)
        assert "url" in response.data[0]

    def test_retrieve_astro_image(self, api_client: APIClient, astro_image: AstroImage) -> None:
        """Test retrieving a single image via the router generated URL"""
        # Detail lookup is now by slug
        url = reverse("astroimages:astroimage-detail", args=[astro_image.slug])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Detail serializer doesn't include ID, check another field
        assert response.data["capture_date"] == str(astro_image.capture_date)
        assert response.data["celestial_object"] == astro_image.celestial_object

    def test_filter_astro_images(self, api_client: APIClient) -> None:
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
    def test_list_background_image(self, api_client: APIClient) -> None:
        """Test retrieving the latest background image"""
        # Create two images, should retrieve the latest one
        MainPageBackgroundImageFactory()
        latest = MainPageBackgroundImageFactory()

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Serializer uses 'url' field mapped from 'image'
        assert latest.path.name in response.data["url"]

    def test_list_background_image_empty(self, api_client: APIClient) -> None:
        """Test retrieving background when none exist"""
        # Ensure clean state
        MainPageBackgroundImage.objects.all().delete()

        url = reverse("astroimages:backgroundImage-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["url"] is None


@pytest.mark.django_db
class TestMainPageLocationViewSet:
    def test_list_active_sliders(self, api_client: APIClient) -> None:
        """Test listing only active sliders."""

        # Create active slider for PL
        place_pl = PlaceFactory(country="PL")
        img_pl = AstroImageFactory(place=place_pl)
        MainPageLocationFactory(place=place_pl, is_active=True, images=[img_pl])

        # Create active slider for US
        place_us = PlaceFactory(country="US")
        img_us = AstroImageFactory(place=place_us)
        MainPageLocationFactory(place=place_us, is_active=True, images=[img_us])

        # Create inactive slider (should not be listed)
        MainPageLocationFactory(place=PlaceFactory(country="NO"), is_active=False)

        url = reverse("astroimages:travel-highlights-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Check existence and basic data
        countries = [item["place"]["country"] for item in response.data]
        assert "Poland" in countries
        assert "United States of America" in countries
        assert "Norway" not in countries

        # Verify structure
        item_pl = next(item for item in response.data if item["place"]["country"] == "Poland")
        assert item_pl["place"]["country"] == "Poland"


@pytest.mark.django_db
class TestTravelHighlightsBySlugView:
    def test_get_by_country_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country slug only."""
        place = PlaceFactory(country="US", name="")  # Explicitly no name for country-only test
        img = AstroImageFactory(place=place, name="USA Image")
        slider = MainPageLocationFactory(place=place, is_active=True)
        slider.images.add(img)

        url = reverse("astroimages:travel-by-country", args=[slider.country_slug])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["place"]["country"] == "United States of America"
        assert not data["place"]["name"]  # might be "" or None
        assert len(data["images"]) >= 1

    def test_get_by_country_and_place_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country and place slug."""
        place = PlaceFactory(name="High Tatras", country="PL")
        img = AstroImageFactory(place=place, name="Tatras 1")
        slider = MainPageLocationFactory(place=place, is_active=True)
        slider.images.add(img)

        url = reverse(
            "astroimages:travel-by-country-place",
            args=[slider.country_slug, slider.place_slug],
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["place"]["country"] == "Poland"
        assert data["place"]["name"] == "High Tatras"
        assert len(data["images"]) == 1
        assert data["images"][0]["name"] == "Tatras 1"

    def test_get_highlights_with_story(self, api_client: APIClient) -> None:
        """Test retrieving highlights with a story"""
        place = PlaceFactory(name="Tatras", country="PL")
        slider = MainPageLocationFactory(place=place, story="A long time ago...")
        AstroImageFactory(place=place)
        slider.images.add(AstroImageFactory(place=place))

        url = reverse(
            "astroimages:travel-by-country-place",
            kwargs={"country_slug": slider.country_slug, "place_slug": slider.place_slug},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["story"] == "A long time ago..."

    def test_get_invalid_slug_returns_404(self, api_client: APIClient) -> None:
        url = reverse("astroimages:travel-by-country", args=["invalid-slug"])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_slider_returns_404(self, api_client: APIClient) -> None:
        slider = MainPageLocationFactory(is_active=False)
        url = reverse("astroimages:travel-by-country", args=[slider.country_slug])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCelestialObjectCategoriesView:
    def test_list_categories(self, api_client: APIClient) -> None:
        """Test retrieving the list of celestial object categories"""

        url = reverse("astroimages:celestial-object-categories")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        expected_categories = [choice[0] for choice in CelestialObjectChoices]
        assert response.data == expected_categories


@pytest.mark.django_db
class TestTagsView:
    def test_list_tags(self, api_client: APIClient) -> None:
        """Test retrieving tags list"""
        url = reverse("astroimages:tags-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_tags_view_category_filtering(self, api_client: APIClient) -> None:
        """Test that tag counts are correctly filtered by celestial_object category."""
        # Create tag objects
        tag_night = TagFactory(name="night")
        tag_galaxy = TagFactory(name="galaxy")

        # Setup: 2 images in different categories sharing the same tag
        img1 = AstroImageFactory(celestial_object="Landscape")
        img1.tags.add(tag_night)

        img2 = AstroImageFactory(celestial_object="Deep Sky")
        img2.tags.add(tag_night, tag_galaxy)

        url = reverse("astroimages:tags-list")

        # 1. No filter - should see all tags with total counts
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        tags_data = {t["slug"]: t["count"] for t in response.data}
        assert tags_data["night"] == 2
        assert tags_data["galaxy"] == 1

        # 2. Filter by Landscape - should only see 'night' tag with count 1
        response = api_client.get(url, {"filter": "Landscape"})
        assert response.status_code == status.HTTP_200_OK
        tags_data = {t["slug"]: t["count"] for t in response.data}
        assert tags_data["night"] == 1
        assert "galaxy" not in tags_data

        # 3. Filter by Deep Sky - should see 'night' and 'galaxy' with count 1
        response = api_client.get(url, {"filter": "Deep Sky"})
        assert response.status_code == status.HTTP_200_OK
        tags_data = {t["slug"]: t["count"] for t in response.data}
        assert tags_data["night"] == 1
        assert tags_data["galaxy"] == 1


@pytest.mark.django_db
class TestAstroImageViewSetCountryPlaceFiltering:
    """
    Test country and place filtering for AstroImageViewSet.
    """

    def test_filter_by_country_code(self, api_client: APIClient) -> None:
        """Test filtering images by country code."""
        place_us = PlaceFactory(country="US")
        place_pl = PlaceFactory(country="PL")
        AstroImageFactory(place=place_us)
        AstroImageFactory(place=place_pl)

        url = reverse("astroimages:astroimage-list")
        response = api_client.get(url, {"country": "US"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "United States" in data[0]["place"]["country"]

    def test_filter_by_country_and_place(self, api_client: APIClient) -> None:
        """Test filtering by both country and place."""
        place_us = PlaceFactory(country="US", name="Hawaii")
        place_us_2 = PlaceFactory(country="US", name="Alaska")
        image_h = AstroImageFactory(place=place_us)
        _ = AstroImageFactory(place=place_us_2)

        url = reverse("astroimages:astroimage-list")

        # Exact match
        response = api_client.get(url, {"country": "US", "place": "Hawaii"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == image_h.name

    def test_travel_param_fuzzy_country_matching(self, api_client: APIClient) -> None:
        """Test fuzzy country matching with travel parameter."""
        place_pl = PlaceFactory(country="PL", name="Tatras")
        AstroImageFactory(place=place_pl)

        url = reverse("astroimages:astroimage-list")
        response = api_client.get(url, {"travel": "Poland"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any("Poland" in img["place"]["country"] for img in data)


@pytest.mark.django_db
class TestSecureMediaView:
    def test_missing_signature_params(self, api_client: APIClient) -> None:
        """Test accessing without s and e parameters returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])

        # Request without params
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Request with only one param
        response = api_client.get(url + "?s=foo")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_signature(self, api_client: APIClient) -> None:
        """Test accessing with manipulated signature returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])
        params = generate_signed_url_params(image.slug)
        params["s"] = "invalid_signature"

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expired_signature(self, api_client: APIClient) -> None:
        """Test accessing with expired timestamp returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])

        # Create params expired 10 seconds ago
        params = generate_signed_url_params(image.slug, expiration_seconds=-10)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_signature_success(self, api_client: APIClient) -> None:
        """Test valid signature returns 200 and X-Accel-Redirect header"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])
        params = generate_signed_url_params(image.slug)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK

        # Verify Nginx redirect header
        assert response.has_header("X-Accel-Redirect")
        assert response["X-Accel-Redirect"].startswith("/protected_media/")
        assert image.path.name in response["X-Accel-Redirect"]

        # Verify Content-Type is empty (let Nginx decide)
        assert response["Content-Type"] == ""

    def test_image_not_found(self, api_client: APIClient) -> None:
        """Test accessing non-existent image with valid signature structure returns 404"""
        slug = "non-existent-slug"
        url = reverse("astroimages:secure-image-serve", args=[slug])
        params = generate_signed_url_params(slug)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_image_file_missing(self, api_client: APIClient) -> None:
        """Test accessing image with no file returns 404"""
        image = AstroImageFactory()
        # Manually clear the path to simulate missing file reference
        image.path = ""
        image.save()

        url = reverse("astroimages:secure-image-serve", args=[image.slug])
        params = generate_signed_url_params(image.slug)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND
