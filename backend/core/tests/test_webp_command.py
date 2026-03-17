from typing import Any

import pytest
from pytest_mock import MockerFixture

from django.core.files.base import ContentFile
from django.core.management import call_command

from astrophotography.tests.factories import AstroImageFactory
from users.models import User
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestConvertImagesToWebpCommand:
    def test_command_converts_images(self, mocker: MockerFixture) -> None:
        """Test that the command iterates correctly and calls conversion."""
        # Setup: Mock conversion result
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_call_command = mocker.patch(
            "core.management.commands.convert_images_to_webp.call_command"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")

        fake_content = ContentFile(b"fake webp content", name="test.webp")
        mock_convert_to_webp.return_value = ("test.jpg", fake_content)
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        # Create objects with actual image content from factory
        astro_img = AstroImageFactory()
        # Ensure User exists and has some images
        user = User.get_user()
        if not user:
            user = UserFactory.create_superuser()

        if not user.avatar:
            user.avatar.save("avatar.jpg", ContentFile(b"fake jpeg"), save=True)

        # Manually set paths to something non-webp if factory generated webp (unlikely but safe)
        if astro_img.path.name.endswith(".webp"):
            astro_img.path.save("test.jpg", ContentFile(b"fake jpeg"), save=True)
        if user.avatar and user.avatar.name.endswith(".webp"):
            user.avatar.save("avatar.jpg", ContentFile(b"fake jpeg"), save=True)

        # Run command
        call_command("convert_images_to_webp")

        # Verify AstroImage was converted
        astro_img.refresh_from_db()
        assert astro_img.path.name.endswith(".webp")
        assert astro_img.legacy_path is not None

        # Verify User avatar was converted
        user.refresh_from_db()
        assert user.avatar.name.endswith(".webp")
        assert user.avatar_legacy is not None

        # Verify cache clearing was called
        mock_call_command.assert_any_call("clear_cache")

    def test_command_dry_run_no_changes(self, mocker: MockerFixture) -> None:
        """Test that --dry-run does not modify the database."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_convert_to_webp.return_value = (
            "test.jpg",
            ContentFile(b"fake webp content", name="test.webp"),
        )
        # Prevent automatic task execution during factory creation for this test
        with mocker.patch("core.models.transaction.on_commit", side_effect=lambda f: None):
            astro_img = AstroImageFactory()
        path_before = astro_img.path.name

        call_command("convert_images_to_webp", dry_run=True)

        astro_img.refresh_from_db()
        assert astro_img.path.name == path_before
        assert not astro_img.legacy_path

    def test_command_force_reconversion(self, mocker: MockerFixture) -> None:
        """Test that --force re-converts already converted images."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        # 1. First conversion
        mock_convert_to_webp.return_value = (
            "test.jpg",
            ContentFile(b"fake webp content", name="test.webp"),
        )
        # Prevent automatic task execution during factory creation for this test
        with mocker.patch("core.models.transaction.on_commit", side_effect=lambda f: None):
            astro_img = AstroImageFactory()
        call_command("convert_images_to_webp")

        astro_img.refresh_from_db()
        assert astro_img.path.name.endswith(".webp")
        assert astro_img.legacy_path == "test.jpg"

        # 2. Second run without force - should skip
        mock_convert_to_webp.reset_mock()
        call_command("convert_images_to_webp")
        mock_convert_to_webp.assert_not_called()

        # 3. Third run with force - should reconvert from legacy_path
        call_command("convert_images_to_webp", force=True)
        # Verify it was called with legacy_path as source
        assert mock_convert_to_webp.called
        # The source should be the legacy_path
        call_args: Any = mock_convert_to_webp.call_args[0][0]
        assert call_args.name == "test.jpg"
