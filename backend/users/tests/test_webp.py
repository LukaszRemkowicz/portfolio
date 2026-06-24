"""Tests for generated-serving methods on the User model."""

from unittest.mock import MagicMock, patch

import pytest

from common.tests.image_helpers import jpeg_field
from core.tasks import process_image_task
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserGetServingImageUrl:
    def test_serves_original_format_variant(self):
        user = UserFactory.create_superuser(avatar=jpeg_field("avatar.jpg", size=(800, 800)))
        variant_file = MagicMock()
        variant_file.url = "/media/avatar.webp"

        with patch.object(
            user,
            "get_variant_file",
            return_value=variant_file,
        ) as get_image_mock:
            url = user.get_serving_image_url("avatar")

        assert url == "/media/avatar.webp"
        get_image_mock.assert_called_once_with(
            "original_format",
            800,
            source_name="avatar",
        )

    def test_falls_back_to_effective_source_when_generated_variant_is_missing(self, caplog):
        user = UserFactory.create_superuser(avatar=jpeg_field("avatar.jpg", size=(800, 800)))
        process_image_task("users", "User", user.pk, ["avatar"])
        user.variants.all().delete()

        url = user.get_serving_image_url("avatar")

        assert ".jpg" in url
        assert "Falling back to source image" in caplog.text

    def test_declares_namespaced_variant_sources_without_thumbnails(self):
        user = UserFactory.create_superuser()

        sources = user.get_image_variant_sources(["avatar", "about_me_image"])

        assert [source.field_name for source in sources] == ["avatar", "about_me_image"]
        assert [source.role_namespace for source in sources] == ["avatar", "about_me_image"]
        specs = user.get_image_variant_specs()

        assert [spec.role for spec in specs] == ["original_format"]
        assert specs[0].quality == 35
