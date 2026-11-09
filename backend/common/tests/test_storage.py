from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest
from rest_framework.test import APIClient

from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from common.storage import R2RoutingStorage, is_private_name
from common.utils.image import file_is_available
from common.utils.signing import generate_signed_url_params

R2 = {
    "R2_ENDPOINT_URL": "https://acct.r2.cloudflarestorage.com",
    "R2_ACCESS_KEY_ID": "k",
    "R2_SECRET_ACCESS_KEY": "s",
    "R2_PUBLIC_BUCKET": "pub",
    "R2_PRIVATE_BUCKET": "priv",
    "R2_PUBLIC_DOMAIN": "media.lukaszremkowicz.com",
    "R2_SIGNED_URL_EXPIRE": 300,
}


@pytest.mark.parametrize(
    ("name", "private"),
    [
        ("images/original/x.png", True),
        ("images/original_format/x.webp", True),
        ("images/detail/x.webp", True),
        ("images/ns/detail/x.webp", True),
        ("images/thumbnail/x.webp", False),
        ("backgrounds/original/x.png", False),
        ("avatars/original_format/x.webp", False),
        ("shop/images/original/x.webp", False),
        ("ckeditor/x.png", False),
    ],
)
def test_is_private_name(name: str, private: bool) -> None:
    assert is_private_name(name) is private


class TestRouting:
    @pytest.fixture(autouse=True)
    def _r2(self, settings: Any) -> None:
        for k, v in R2.items():
            setattr(settings, k, v)

    def test_urls_and_routing(self) -> None:
        storage = R2RoutingStorage()
        public = storage.url("images/thumbnail/x.webp")
        assert public == "https://media.lukaszremkowicz.com/images/thumbnail/x.webp"
        private = storage.url("images/original/x.png")
        assert "X-Amz-Signature" in private
        assert urlparse(private).hostname.endswith("acct.r2.cloudflarestorage.com")

    def test_ops_hit_right_backend(self) -> None:
        storage = R2RoutingStorage()
        storage._public, storage._private = MagicMock(), MagicMock()
        storage._save("images/detail/x.webp", b"")
        storage._private._save.assert_called_once()
        storage.exists("images/thumbnail/x.webp")
        storage._public.exists.assert_called_once_with("images/thumbnail/x.webp")
        storage.delete("images/original/x.png")
        storage._private.delete.assert_called_once()
        storage._public.delete.assert_not_called()

    def test_read_path_skips_exists(self) -> None:
        storage = R2RoutingStorage()
        storage._public = MagicMock()
        field = SimpleNamespace(name="images/thumbnail/x.webp", storage=storage)
        assert file_is_available(field)  # type: ignore[arg-type]
        storage._public.exists.assert_not_called()
        empty = SimpleNamespace(name="", storage=storage)
        assert not file_is_available(empty)  # type: ignore[arg-type]

    def test_original_fallback_never_returns_private_url(self) -> None:
        from core.models import BaseImage

        storage = R2RoutingStorage()
        storage._private = MagicMock()
        original = SimpleNamespace(name="images/original/x.png", storage=storage)
        image = SimpleNamespace(original=original)
        assert BaseImage.get_original_image_url(image) is None  # type: ignore[arg-type]
        storage._private.url.assert_not_called()


@pytest.mark.django_db
def test_secure_view_redirects_in_remote_mode(api_client: APIClient) -> None:
    image = AstroImageFactory(original__width=3000, original__height=2000)
    fake: Any = SimpleNamespace(remote=True, url=lambda n: f"https://signed.example/{n}")
    with patch("core.views.default_storage", fake):
        response = api_client.get(
            reverse("astroimages:secure-image-serve", args=[image.slug]),
            generate_signed_url_params(image.slug),
        )
    assert response.status_code == 302
    assert response["Location"].startswith("https://signed.example/")
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert not response.has_header("X-Accel-Redirect")
