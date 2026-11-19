# backend/astrophotography/tests/test_views.py
from http import HTTPStatus
from typing import Any

import pytest

from django.test import Client
from django.urls import reverse

from astrophotography.models import AstroImage
from common.utils.signing import generate_signed_url_params


def _admin_media_url(astro_image: AstroImage) -> str:
    return reverse(
        "admin-astroimage-secure-media",
        kwargs={"pk": str(astro_image.pk), "field_name": "original"},
    )


def _signature_id(astro_image: AstroImage) -> str:
    return f"admin_media_astrophotography_astroimage_{astro_image.pk}_original"


@pytest.mark.django_db
class TestAstroImageAdminSecureMediaView:
    def test_success_staff(self, admin_client: Client, astro_image: AstroImage) -> None:
        params: dict[str, Any] = generate_signed_url_params(_signature_id(astro_image))
        response = admin_client.get(_admin_media_url(astro_image), params)
        astro_image.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert response["Cache-Control"] == "private, no-store, max-age=0"
        assert not response.has_header("X-Accel-Redirect")
        assert response["Content-Disposition"].startswith("inline;")
        with astro_image.original.open("rb") as f:
            assert b"".join(response.streaming_content) == f.read()

    def test_forbidden_anonymous(self, client: Client, astro_image: AstroImage) -> None:
        params: dict[str, Any] = generate_signed_url_params(_signature_id(astro_image))
        response = client.get(_admin_media_url(astro_image), params)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_missing_signature_staff(self, admin_client: Client, astro_image: AstroImage) -> None:
        response = admin_client.get(_admin_media_url(astro_image))
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_invalid_signature_staff(self, admin_client: Client, astro_image: AstroImage) -> None:
        params: dict[str, Any] = generate_signed_url_params(_signature_id(astro_image))
        params["s"] = "invalid_hash"
        response = admin_client.get(_admin_media_url(astro_image), params)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_expired_signature_staff(self, admin_client: Client, astro_image: AstroImage) -> None:
        params: dict[str, Any] = generate_signed_url_params(
            _signature_id(astro_image), expiration_seconds=-10
        )
        response = admin_client.get(_admin_media_url(astro_image), params)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post_not_allowed(self, admin_client: Client, astro_image: AstroImage) -> None:
        response = admin_client.post(_admin_media_url(astro_image))
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
