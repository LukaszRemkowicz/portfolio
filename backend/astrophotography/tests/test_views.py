# backend/astrophotography/tests/test_views.py
from typing import Any

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.models import (
    AstroImage,
    MainPageBackgroundImage,
    MainPageLocation,
    Place,
    Tag,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
    TagFactory,
)
from astrophotography.utils import get_celestial_categories
from common.utils.signing import generate_signed_url_params

# URL Names
ASTROIMAGE_LIST_URL_NAME: str = "astroimages:astroimage-list"
ASTROIMAGE_DETAIL_URL_NAME: str = "astroimages:astroimage-detail"
BACKGROUND_IMAGE_LIST_URL_NAME: str = "astroimages:backgroundImage-list"
TRAVEL_HIGHLIGHTS_LIST_URL_NAME: str = "astroimages:travel-highlights-list"
TRAVEL_BY_COUNTRY_URL_NAME: str = "astroimages:travel-by-country"
TRAVEL_BY_COUNTRY_PLACE_URL_NAME: str = "astroimages:travel-by-country-place"
CELESTIAL_CATEGORIES_URL_NAME: str = "astroimages:celestial-object-categories"
TAGS_LIST_URL_NAME: str = "astroimages:tags-list"
SECURE_IMAGE_SERVE_URL_NAME: str = "astroimages:secure-image-serve"


@pytest.mark.django_db
class TestAstroImageViewSet:
    def test_list_astro_images(self, api_client: APIClient, astro_image: AstroImage) -> None:
        """Test listing images via the router generated URL"""
        url: str = reverse(ASTROIMAGE_LIST_URL_NAME)
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["pk"] == str(astro_image.pk)
        # After Phase 2: URL field removed, served via /v1/images/

    def test_retrieve_astro_image(self, api_client: APIClient, astro_image: AstroImage) -> None:
        """Test retrieving a single image via the router generated URL"""
        # Detail lookup is now by slug
        url: str = reverse(ASTROIMAGE_DETAIL_URL_NAME, args=[astro_image.slug])
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Detail serializer doesn't include ID, check another field
        assert response.data["capture_date"] == str(astro_image.capture_date)
        assert response.data["celestial_object"] == astro_image.celestial_object

    def test_filter_astro_images(self, api_client: APIClient) -> None:
        """Test filtering images by celestial_object"""
        AstroImageFactory(celestial_object="Deep Sky")
        AstroImageFactory(celestial_object="Deep Sky")
        AstroImageFactory(celestial_object="Landscape")

        url: str = reverse(ASTROIMAGE_LIST_URL_NAME)

        # Filter matching "Deep Sky"
        response: Response = api_client.get(url, {"filter": "Deep Sky"})
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
        latest: MainPageBackgroundImage = MainPageBackgroundImageFactory()

        url: str = reverse(BACKGROUND_IMAGE_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Serializer uses 'url' field mapped from 'image'
        assert latest.path.name in response.data["url"]

    def test_list_background_image_empty(self, api_client: APIClient) -> None:
        """Test retrieving background when none exist"""
        # Ensure clean state
        MainPageBackgroundImage.objects.all().delete()

        url: str = reverse(BACKGROUND_IMAGE_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["url"] is None


@pytest.mark.django_db
class TestMainPageLocationViewSet:
    def test_list_active_sliders(self, api_client: APIClient) -> None:
        """Test listing only active sliders."""

        # Create active slider for PL
        place_pl: Place = PlaceFactory(country="PL")
        img_pl: AstroImage = AstroImageFactory(place=place_pl)
        MainPageLocationFactory(place=place_pl, is_active=True, images=[img_pl])

        # Create active slider for US
        place_us: Place = PlaceFactory(country="US")
        img_us: AstroImage = AstroImageFactory(place=place_us)
        MainPageLocationFactory(place=place_us, is_active=True, images=[img_us])

        # Create inactive slider (should not be listed)
        MainPageLocationFactory(place=PlaceFactory(country="NO"), is_active=False)

        url: str = reverse(TRAVEL_HIGHLIGHTS_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Check existence and basic data
        countries: list[str] = [item["place"]["country"] for item in response.data]
        assert "Poland" in countries
        assert "United States of America" in countries
        assert "Norway" not in countries

        # Verify structure
        item_pl: dict[str, Any] = next(
            item for item in response.data if item["place"]["country"] == "Poland"
        )
        assert item_pl["place"]["country"] == "Poland"


@pytest.mark.django_db
class TestTravelHighlightsBySlugView:
    def test_get_by_country_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country slug only."""
        place: Place = PlaceFactory(
            country="US", name=""
        )  # Explicitly no name for country-only test
        img: AstroImage = AstroImageFactory(place=place, name="USA Image")
        slider: MainPageLocation = MainPageLocationFactory(place=place, is_active=True)
        slider.images.add(img)

        url: str = reverse(TRAVEL_BY_COUNTRY_URL_NAME, args=[slider.country_slug])
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()
        assert data["place"]["country"] == "United States of America"
        assert not data["place"]["name"]  # might be "" or None
        assert len(data["images"]) >= 1

    def test_get_by_country_and_place_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country and place slug."""
        place: Place = PlaceFactory(name="High Tatras", country="PL")
        img: AstroImage = AstroImageFactory(place=place, name="Tatras 1")
        slider: MainPageLocation = MainPageLocationFactory(place=place, is_active=True)
        slider.images.add(img)

        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_URL_NAME,
            args=[slider.country_slug, slider.place_slug],
        )
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()
        assert data["place"]["country"] == "Poland"
        assert data["place"]["name"] == "High Tatras"
        assert len(data["images"]) == 1
        assert data["images"][0]["name"] == "Tatras 1"

    def test_get_highlights_with_story(self, api_client: APIClient) -> None:
        """Test retrieving highlights with a story"""
        place: Place = PlaceFactory(name="Tatras", country="PL")
        slider: MainPageLocation = MainPageLocationFactory(place=place, story="A long time ago...")
        AstroImageFactory(place=place)
        slider.images.add(AstroImageFactory(place=place))

        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_URL_NAME,
            kwargs={"country_slug": slider.country_slug, "place_slug": slider.place_slug},
        )
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["story"] == "A long time ago..."

    def test_get_invalid_slug_returns_404(self, api_client: APIClient) -> None:
        url: str = reverse(TRAVEL_BY_COUNTRY_URL_NAME, args=["invalid-slug"])
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_slider_returns_404(self, api_client: APIClient) -> None:
        slider: MainPageLocation = MainPageLocationFactory(is_active=False)
        url: str = reverse(TRAVEL_BY_COUNTRY_URL_NAME, args=[slider.country_slug])
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCelestialObjectCategoriesView:
    def test_list_categories(self, api_client: APIClient) -> None:
        """Test retrieving the list of celestial object categories"""

        url: str = reverse(CELESTIAL_CATEGORIES_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        assert response.data == get_celestial_categories()


@pytest.mark.django_db
class TestTagsView:
    def test_list_tags(self, api_client: APIClient) -> None:
        """Test retrieving tags list"""
        url: str = reverse(TAGS_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_tags_view_category_filtering(self, api_client: APIClient) -> None:
        """Test that tag counts are correctly filtered by celestial_object category."""
        # Create tag objects
        tag_night: Tag = TagFactory(name="night")
        tag_galaxy: Tag = TagFactory(name="galaxy")

        # Setup: 2 images in different categories sharing the same tag
        img1: AstroImage = AstroImageFactory(celestial_object="Landscape")
        img1.tags.add(tag_night)

        img2: AstroImage = AstroImageFactory(celestial_object="Deep Sky")
        img2.tags.add(tag_night, tag_galaxy)

        url: str = reverse(TAGS_LIST_URL_NAME)

        # 1. No filter - should see all tags with total counts
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        tags_data: dict[str, int] = {t["slug"]: t["count"] for t in response.data}
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
        place_us: Place = PlaceFactory(country="US")
        place_pl: Place = PlaceFactory(country="PL")
        AstroImageFactory(place=place_us)
        AstroImageFactory(place=place_pl)

        url: str = reverse(ASTROIMAGE_LIST_URL_NAME)
        response: Response = api_client.get(url, {"country": "US"})

        assert response.status_code == status.HTTP_200_OK
        data: list[dict[str, Any]] = response.json()
        assert len(data) == 1
        assert "United States" in data[0]["place"]["country"]

    def test_filter_by_country_and_place(self, api_client: APIClient) -> None:
        """Test filtering by both country and place."""
        place_us: Place = PlaceFactory(country="US", name="Hawaii")
        place_us_2: Place = PlaceFactory(country="US", name="Alaska")
        image_h: AstroImage = AstroImageFactory(place=place_us)
        _ = AstroImageFactory(place=place_us_2)

        url: str = reverse(ASTROIMAGE_LIST_URL_NAME)

        # Exact match
        response: Response = api_client.get(url, {"country": "US", "place": "Hawaii"})
        assert response.status_code == status.HTTP_200_OK
        data: list[dict[str, Any]] = response.json()
        assert len(data) == 1
        assert data[0]["name"] == image_h.name

    def test_travel_param_fuzzy_country_matching(self, api_client: APIClient) -> None:
        """Test fuzzy country matching with travel parameter."""
        place_pl: Place = PlaceFactory(country="PL", name="Tatras")
        AstroImageFactory(place=place_pl)

        url: str = reverse(ASTROIMAGE_LIST_URL_NAME)
        response: Response = api_client.get(url, {"travel": "Poland"})

        assert response.status_code == status.HTTP_200_OK
        data: list[dict[str, Any]] = response.json()
        assert len(data) >= 1
        assert any("Poland" in img["place"]["country"] for img in data)


@pytest.mark.django_db
class TestSecureMediaView:
    def test_missing_signature_params(self, api_client: APIClient) -> None:
        """Test accessing without s and e parameters returns 403"""
        image: AstroImage = AstroImageFactory()
        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[image.slug])

        # Request without params
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Request with only one param
        response = api_client.get(url + "?s=foo")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_signature(self, api_client: APIClient) -> None:
        """Test accessing with manipulated signature returns 403"""
        image: AstroImage = AstroImageFactory()
        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[image.slug])
        params: dict[str, Any] = generate_signed_url_params(image.slug)
        params["s"] = "invalid_signature"

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expired_signature(self, api_client: APIClient) -> None:
        """Test accessing with expired timestamp returns 403"""
        image: AstroImage = AstroImageFactory()
        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[image.slug])

        # Create params expired 10 seconds ago
        params: dict[str, Any] = generate_signed_url_params(image.slug, expiration_seconds=-10)

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_signature_success(self, api_client: APIClient) -> None:
        """Test valid signature returns 200 and X-Accel-Redirect header"""
        image: AstroImage = AstroImageFactory()
        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[image.slug])
        params: dict[str, Any] = generate_signed_url_params(image.slug)

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK

        # Verify Nginx redirect header
        assert response.has_header("X-Accel-Redirect")
        assert response["X-Accel-Redirect"].startswith("/protected_media/")
        assert image.path.name in response["X-Accel-Redirect"]

        # Verify Content-Type is empty (let Nginx decide)
        assert response["Content-Type"] == ""

    def test_image_not_found(self, api_client: APIClient) -> None:
        """Test accessing non-existent image with valid signature structure returns 404"""
        slug: str = "non-existent-slug"
        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[slug])
        params: dict[str, Any] = generate_signed_url_params(slug)

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_image_file_missing(self, api_client: APIClient) -> None:
        """Test accessing image with no file returns 404"""
        image: AstroImage = AstroImageFactory()
        # Manually clear the path to simulate missing file reference
        image.path = ""
        image.save()

        url: str = reverse(SECURE_IMAGE_SERVE_URL_NAME, args=[image.slug])
        params: dict[str, Any] = generate_signed_url_params(image.slug)

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND
