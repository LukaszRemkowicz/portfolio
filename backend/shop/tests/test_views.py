import uuid
from http import HTTPStatus
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

from django.test import Client
from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import jpeg_field
from core.tests.factories import ImageVariantFactory


@pytest.mark.django_db
class TestShopAstroImageLookupView:
    def test_lookup_returns_signed_original_url_for_admin_cropper(
        self, admin_client: Client
    ) -> None:
        with patch("core.models.submit"):
            image = AstroImageFactory(original=jpeg_field("lookup-thumb.jpg", size=(1200, 800)))
        ImageVariantFactory(
            owner=image,
            file__filename="lookup-thumb.webp",
            role="thumbnail",
            width=560,
            height=373,
        )

        response = admin_client.get(reverse("shop-image-lookup"), {"id": image.pk})

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        parsed_url = urlparse(data["url"])
        assert parsed_url.path == (
            f"/v1/admin/media/astrophotography/astroimage/{image.pk}/original/"
        )
        assert "s=" in parsed_url.query
        assert "e=" in parsed_url.query
        assert data["source_name"] == image.original.name
        assert data["mime_type"] == "image/jpeg"

    def test_lookup_returns_404_when_original_field_is_empty(self, admin_client: Client) -> None:
        with patch("core.models.submit"):
            image = AstroImageFactory(original=None)

        response = admin_client.get(reverse("shop-image-lookup"), {"id": image.pk})

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["error"] == "Original image field is empty"

    def test_lookup_returns_404_for_unknown_id(self, admin_client: Client) -> None:
        response = admin_client.get(reverse("shop-image-lookup"), {"id": uuid.uuid4()})

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_lookup_returns_400_without_id(self, admin_client: Client) -> None:
        response = admin_client.get(reverse("shop-image-lookup"))

        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_lookup_rejects_unsafe_methods(self, admin_client: Client, method: str) -> None:
        response = getattr(admin_client, method)(reverse("shop-image-lookup"))

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_lookup_hidden_from_non_staff(self, client: Client) -> None:
        image = AstroImageFactory()
        response = client.get(reverse("shop-image-lookup"), {"id": image.pk})
        assert response.status_code == 404
