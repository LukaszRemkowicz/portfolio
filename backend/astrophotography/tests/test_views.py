# backend/astrophotography/tests/test_views.py
from datetime import date
from typing import Any

import pytest
from psycopg2.extras import DateRange
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
from common.constants import FALLBACK_URL_SLUG
from common.utils.signing import generate_signed_url_params

# URL Names
ASTROIMAGE_LIST_URL_NAME: str = "astroimages:astroimage-list"
ASTROIMAGE_DETAIL_URL_NAME: str = "astroimages:astroimage-detail"
BACKGROUND_IMAGE_LIST_URL_NAME: str = "astroimages:backgroundImage-list"
TRAVEL_HIGHLIGHTS_LIST_URL_NAME: str = "astroimages:travel-highlights-list"
TRAVEL_BY_COUNTRY_URL_NAME: str = "astroimages:travel-by-country"
TRAVEL_BY_COUNTRY_PLACE_URL_NAME: str = "astroimages:travel-by-country-place"
TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME: str = "astroimages:travel-by-country-place-date"
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

    def test_latest_astro_images(self, api_client: APIClient) -> None:
        """Test the dedicated 'latest' endpoint returns exactly 9 images."""
        # Create 12 images
        for _ in range(12):
            AstroImageFactory()

        url: str = reverse("astroimages:astroimage-latest")
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 9


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
    def test_missing_segments_returns_404(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country slug only returns 404 (needs 3 segments)."""
        place: Place = PlaceFactory(country="US", name="No Date")
        slider: MainPageLocation = MainPageLocationFactory(place=place, is_active=True)

        url: str = f"/v1/travel/{slider.country_slug}/"
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        url2: str = f"/v1/travel/{slider.country_slug}/{slider.place_slug}/"
        response2: Response = api_client.get(url2)

        assert response2.status_code == status.HTTP_404_NOT_FOUND

    def test_get_by_country_and_place_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights by country, place, and date slug."""

        place: Place = PlaceFactory(name="High Tatras", country="PL")
        img: AstroImage = AstroImageFactory(place=place, name="Tatras 1")
        slider: MainPageLocation = MainPageLocationFactory(
            place=place,
            is_active=True,
            adventure_date=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
        )
        slider.images.add(img)

        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            kwargs={
                "country_slug": slider.country_slug,
                "place_slug": slider.place_slug,
                "date_slug": slider.date_slug,
            },
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
        slider: MainPageLocation = MainPageLocationFactory(
            place=place,
            story="A long time ago...",
            adventure_date=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
        )
        AstroImageFactory(place=place)
        slider.images.add(AstroImageFactory(place=place))

        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            kwargs={
                "country_slug": slider.country_slug,
                "place_slug": slider.place_slug,
                "date_slug": slider.date_slug,
            },
        )
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["story"] == "A long time ago..."

    def test_get_invalid_slug_returns_404(self, api_client: APIClient) -> None:
        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            kwargs={
                "country_slug": "invalid",
                "place_slug": "invalid",
                "date_slug": "invalid",
            },
        )
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_slider_returns_404(self, api_client: APIClient) -> None:
        place: Place = PlaceFactory(name="Valid", country="PL")
        slider: MainPageLocation = MainPageLocationFactory(place=place, is_active=False)
        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            kwargs={
                "country_slug": slider.country_slug,
                "place_slug": slider.place_slug,
                "date_slug": slider.date_slug,
            },
        )
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_highlights_without_place_fallback_slug(self, api_client: APIClient) -> None:
        """Test retrieving highlights when no place is assigned, using 'explore'."""

        slider: MainPageLocation = MainPageLocationFactory(
            place=None,
            country_slug="namibia",
            is_active=True,
            adventure_date=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
        )

        url: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            kwargs={
                "country_slug": FALLBACK_URL_SLUG,
                "place_slug": FALLBACK_URL_SLUG,
                "date_slug": slider.date_slug,
            },
        )
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["place_slug"] == FALLBACK_URL_SLUG

    def test_two_adventures_same_place_accessible_by_date_slug(self, api_client: APIClient) -> None:
        """Two adventures at the same place must each be reachable via their date slug."""

        place: Place = PlaceFactory(name="Hakos", country="NA")

        slider_jan: MainPageLocation = MainPageLocationFactory(
            place=place,
            is_active=True,
            adventure_date=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
        )
        slider_aug: MainPageLocation = MainPageLocationFactory(
            place=place,
            is_active=True,
            adventure_date=DateRange(date(2026, 8, 1), date(2026, 8, 31)),
        )

        # Access the January 2024 adventure
        url_jan: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            args=[slider_jan.country_slug, slider_jan.place_slug, "jan2024"],
        )
        response_jan: Response = api_client.get(url_jan)
        assert response_jan.status_code == status.HTTP_200_OK
        assert response_jan.json()["pk"] == slider_jan.pk

        # Access the August 2026 adventure
        url_aug: str = reverse(
            TRAVEL_BY_COUNTRY_PLACE_DATE_URL_NAME,
            args=[slider_aug.country_slug, slider_aug.place_slug, "aug2026"],
        )
        response_aug: Response = api_client.get(url_aug)
        assert response_aug.status_code == status.HTTP_200_OK
        assert response_aug.json()["pk"] == slider_aug.pk

    def test_date_slug_serializer_field_present(self, api_client: APIClient) -> None:
        """date_slug must be included in the list response for each MainPageLocation."""

        place: Place = PlaceFactory(name="Tatry", country="PL")
        slider: MainPageLocation = MainPageLocationFactory(
            place=place,
            is_active=True,
            adventure_date=DateRange(date(2026, 1, 1), date(2026, 1, 31)),
        )

        url: str = reverse(TRAVEL_HIGHLIGHTS_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        location_data = next(item for item in response.data if str(item["pk"]) == str(slider.pk))
        assert location_data["date_slug"] == "jan2026"

    def test_missing_segments_fails(self, api_client: APIClient) -> None:
        """Without date_slug or place_slug, the endpoint returns 404 (needs all 3)."""

        place: Place = PlaceFactory(name="Hakos", country="NA")
        slider: MainPageLocation = MainPageLocationFactory(
            place=place,
            is_active=True,
            adventure_date=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
        )

        # 2 segments (country/place) -> 404
        url_2_seg: str = f"/v1/travel/{slider.country_slug}/{slider.place_slug}/"
        response_2_seg: Response = api_client.get(url_2_seg)
        assert response_2_seg.status_code == status.HTTP_404_NOT_FOUND

        # 1 segment (country) -> 404
        url_1_seg: str = f"/v1/travel/{slider.country_slug}/"
        response_1_seg: Response = api_client.get(url_1_seg)
        assert response_1_seg.status_code == status.HTTP_404_NOT_FOUND


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
class TestAstroImageSecureView:
    """
    Tests the AstroImageSecureView to verify that high-resolution
    objects are protected and correctly authenticated via cryptographic signature.
    """

    def test_astro_image_secure_view_success(
        self, api_client: APIClient, astro_image: AstroImage
    ) -> None:
        url: str = reverse("astroimages:secure-image-serve", args=[astro_image.slug])
        params: dict[str, Any] = generate_signed_url_params(astro_image.slug)

        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK
        assert response.has_header("X-Accel-Redirect")
        assert f"/protected_media/{astro_image.path.name}" == response["X-Accel-Redirect"]

    def test_secure_media_view_missing_signature(
        self, api_client: APIClient, astro_image: AstroImage
    ) -> None:
        """Test base class validation logic implicitly via a subclass"""
        url: str = reverse("astroimages:secure-image-serve", args=[astro_image.slug])
        response: Response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_secure_media_view_invalid_signature(
        self, api_client: APIClient, astro_image: AstroImage
    ) -> None:
        url: str = reverse("astroimages:secure-image-serve", args=[astro_image.slug])
        params: dict[str, Any] = generate_signed_url_params(astro_image.slug)
        params["s"] = "invalid_hash"
        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_secure_media_view_expired_signature(
        self, api_client: APIClient, astro_image: AstroImage
    ) -> None:
        url: str = reverse("astroimages:secure-image-serve", args=[astro_image.slug])
        params: dict[str, Any] = generate_signed_url_params(
            astro_image.slug, expiration_seconds=-10
        )
        response: Response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN
