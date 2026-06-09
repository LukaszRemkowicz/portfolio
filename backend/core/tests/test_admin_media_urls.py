from unittest.mock import patch

import pytest

from django.conf import settings
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

    def test_blocks_images_directory(self):
        request = self.factory.get(
            "/media/images/example.jpg",
            HTTP_HOST=settings.ADMIN_DOMAIN,
        )

        with pytest.raises(Http404):
            safe_serve(request, "images/example.jpg", document_root="/tmp")

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
