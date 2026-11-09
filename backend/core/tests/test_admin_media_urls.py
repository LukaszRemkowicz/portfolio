from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse
from django.test import RequestFactory, SimpleTestCase

from settings.urls import safe_serve


class SafeServeTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_blocks_logs_directory(self):
        request = self.factory.get(
            "/media/logs/example.txt",
            HTTP_HOST=settings.ADMIN_DOMAIN,
        )

        with pytest.raises(Http404):
            safe_serve(request, "logs/example.txt", document_root="/tmp")

    def test_blocks_private_images_for_unauthenticated_users(self):
        for path in (
            "images/original/source.jpg",
            "images/legacy-source.jpg",
            "images/high_resolution/full.webp",
            "images/original_format/old-full.webp",
        ):
            with self.subTest(path=path):
                request = self.factory.get(f"/media/{path}", HTTP_HOST=settings.ADMIN_DOMAIN)
                request.user = AnonymousUser()

                with patch("settings.urls.serve", return_value=HttpResponse("ok")) as mock_serve:
                    with pytest.raises(Http404):
                        safe_serve(request, path, document_root="/tmp")
                mock_serve.assert_not_called()

    def test_allows_publicly_generated_image_variants(self):
        for path in ("images/thumbnail/example.webp", "images/detail/example.webp"):
            with self.subTest(path=path):
                request = self.factory.get(f"/media/{path}", HTTP_HOST=settings.ADMIN_DOMAIN)
                request.user = AnonymousUser()

                with patch("settings.urls.serve", return_value=HttpResponse("ok")) as mock_serve:
                    response = safe_serve(request, path, document_root="/tmp")

                assert response.status_code == 200
                mock_serve.assert_called_once_with(
                    request, path, document_root="/tmp", show_indexes=False
                )

    def test_allows_private_images_to_authenticated_staff(self):
        path = "images/original/source.jpg"
        request = self.factory.get(f"/media/{path}", HTTP_HOST=settings.ADMIN_DOMAIN)
        request.user = SimpleNamespace(is_authenticated=True, is_staff=True)

        with patch("settings.urls.serve", return_value=HttpResponse("ok")) as mock_serve:
            response = safe_serve(request, path, document_root="/tmp")

        assert response.status_code == 200
        mock_serve.assert_called_once_with(request, path, document_root="/tmp", show_indexes=False)
        cache_control = response.headers.get("Cache-Control", "").lower()
        assert "private" in cache_control
        assert "no-store" in cache_control
        assert "max-age=0" in cache_control
        assert "cookie" in response.headers.get("Vary", "").lower()

    def test_blocks_public_prefix_traversal_into_private_images(self):
        path = "about_me_images/../images/original/source.jpg"
        request = self.factory.get(f"/media/{path}", HTTP_HOST=settings.ADMIN_DOMAIN)
        request.user = AnonymousUser()

        with patch("settings.urls.serve", return_value=HttpResponse("ok")) as mock_serve:
            with pytest.raises(Http404):
                safe_serve(request, path, document_root="/tmp")
        mock_serve.assert_not_called()

    @patch("settings.urls.serve", return_value=HttpResponse("ok"))
    def test_allows_about_me_images_directory(self, mock_serve):
        request = self.factory.get(
            "/media/about_me_images/example.jpg",
            HTTP_HOST=settings.ADMIN_DOMAIN,
        )

        response = safe_serve(request, "about_me_images/example.jpg", document_root="/tmp")

        assert response.status_code == 200
        mock_serve.assert_called_once_with(
            request,
            "about_me_images/example.jpg",
            document_root="/tmp",
            show_indexes=False,
        )

    def test_blocks_non_admin_host(self):
        request = self.factory.get(
            "/media/about_me_images/example.jpg",
            HTTP_HOST=settings.SITE_DOMAIN,
        )

        with pytest.raises(Http404):
            safe_serve(request, "about_me_images/example.jpg", document_root="/tmp")
