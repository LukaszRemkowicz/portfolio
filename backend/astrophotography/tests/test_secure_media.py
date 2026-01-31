import pytest
from rest_framework import status

from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from core.utils.signing import generate_signed_url_params


@pytest.mark.django_db
class TestSecureMediaView:
    def test_missing_signature_params(self, api_client):
        """Test accessing without s and e parameters returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])

        # Request without params
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Request with only one param
        response = api_client.get(url + "?s=foo")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_signature(self, api_client):
        """Test accessing with manipulated signature returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])
        params = generate_signed_url_params(image.slug)
        params["s"] = "invalid_signature"

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expired_signature(self, api_client):
        """Test accessing with expired timestamp returns 403"""
        image = AstroImageFactory()
        url = reverse("astroimages:secure-image-serve", args=[image.slug])

        # Create params expired 10 seconds ago
        params = generate_signed_url_params(image.slug, expiration_seconds=-10)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_valid_signature_success(self, api_client):
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

    def test_image_not_found(self, api_client):
        """Test accessing non-existent image with valid signature structure returns 404"""
        slug = "non-existent-slug"
        url = reverse("astroimages:secure-image-serve", args=[slug])
        params = generate_signed_url_params(slug)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_image_file_missing(self, api_client):
        """Test accessing image with no file returns 404"""
        image = AstroImageFactory()
        # Manually clear the path to simulate missing file reference
        image.path = ""
        image.save()

        url = reverse("astroimages:secure-image-serve", args=[image.slug])
        params = generate_signed_url_params(image.slug)

        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND
