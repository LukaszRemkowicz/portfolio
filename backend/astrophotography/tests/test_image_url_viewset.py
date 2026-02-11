# backend/astrophotography/tests/test_image_url_viewset.py
"""Tests for ImageURLViewSet - the /v1/images/ endpoint that serves signed URLs."""

from urllib.parse import parse_qs, urlparse

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory

IMAGE_URL_LIST_URL_NAME: str = "astroimages:image-urls-list"
IMAGE_URL_DETAIL_URL_NAME: str = "astroimages:image-urls-detail"


@pytest.mark.django_db
class TestImageURLViewSet:
    """Test suite for the ImageURLViewSet (/v1/images/ endpoint)."""

    def test_list_returns_url_mapping(self, api_client: APIClient) -> None:
        """Test that list endpoint returns {slug: signed_url} mapping."""
        # Create test images
        AstroImageFactory(slug="orion-nebula")
        AstroImageFactory(slug="andromeda-galaxy")
        AstroImageFactory(slug="milky-way-arch")

        url: str = reverse(IMAGE_URL_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert len(response.data) == 3

        # Verify all slugs are present
        assert "orion-nebula" in response.data
        assert "andromeda-galaxy" in response.data
        assert "milky-way-arch" in response.data

        # Verify URLs are signed (contain signature params)
        for slug, signed_url in response.data.items():
            assert isinstance(signed_url, str)
            assert "/serve/" in signed_url
            parsed = urlparse(signed_url)
            query_params = parse_qs(parsed.query)
            assert "s" in query_params  # signature
            assert "e" in query_params  # expiration

    def test_list_returns_empty_for_no_images(self, api_client: APIClient) -> None:
        """Test that list endpoint returns empty dict when no images exist."""
        url: str = reverse(IMAGE_URL_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_retrieve_returns_signed_url(self, api_client: APIClient) -> None:
        """Test that retrieve endpoint returns signed URL for a single image."""
        AstroImageFactory(slug="horsehead-nebula")

        url: str = reverse(IMAGE_URL_DETAIL_URL_NAME, kwargs={"pk": "horsehead-nebula"})
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "url" in response.data
        assert isinstance(response.data["url"], str)

        # Verify URL is signed
        signed_url = response.data["url"]
        assert "/serve/" in signed_url
        parsed = urlparse(signed_url)
        query_params = parse_qs(parsed.query)
        assert "s" in query_params  # signature
        assert "e" in query_params  # expiration

    def test_retrieve_returns_404_for_nonexistent_image(self, api_client: APIClient) -> None:
        """Test that retrieve endpoint returns 404 for non-existent slug."""
        url: str = reverse(IMAGE_URL_DETAIL_URL_NAME, kwargs={"pk": "nonexistent-slug"})
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_urls_are_absolute(self, api_client: APIClient) -> None:
        """Test that returned URLs are absolute (include domain)."""
        AstroImageFactory(slug="test-image")

        url: str = reverse(IMAGE_URL_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        signed_url = response.data["test-image"]

        # URL should be absolute (start with http:// or https://)
        assert signed_url.startswith("http://") or signed_url.startswith("https://")

    def test_retrieve_url_is_absolute(self, api_client: APIClient) -> None:
        """Test that retrieve endpoint returns absolute URL."""
        AstroImageFactory(slug="test-image")

        url: str = reverse(IMAGE_URL_DETAIL_URL_NAME, kwargs={"pk": "test-image"})
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        signed_url = response.data["url"]

        # URL should be absolute
        assert signed_url.startswith("http://") or signed_url.startswith("https://")

    def test_list_endpoint_not_cached(self, api_client: APIClient) -> None:
        """Test that list endpoint does NOT have cache headers."""
        AstroImageFactory(slug="test-image")

        url: str = reverse(IMAGE_URL_LIST_URL_NAME)
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Should NOT have cache-control header with long timeout
        # (or should have no-cache/no-store)
        cache_control = response.get("Cache-Control", "")
        # If cache-control exists, it should not have a long max-age
        if "max-age" in cache_control:
            # Extract max-age value
            import re

            match = re.search(r"max-age=(\d+)", cache_control)
            if match:
                max_age = int(match.group(1))
                # Should not be cached for more than a few seconds
                assert max_age < 60, "URL endpoint should not be cached long-term"

    def test_retrieve_endpoint_not_cached(self, api_client: APIClient) -> None:
        """Test that retrieve endpoint does NOT have cache headers."""
        AstroImageFactory(slug="test-image")

        url: str = reverse(IMAGE_URL_DETAIL_URL_NAME, kwargs={"pk": "test-image"})
        response: Response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Should NOT have cache-control header with long timeout
        cache_control = response.get("Cache-Control", "")
        if "max-age" in cache_control:
            import re

            match = re.search(r"max-age=(\d+)", cache_control)
            if match:
                max_age = int(match.group(1))
                assert max_age < 60, "URL endpoint should not be cached long-term"
